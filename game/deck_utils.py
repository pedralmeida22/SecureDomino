import random
import string
from security import encodeBase64, SymCipher, decodeBase64, AsymCipher
import hmac
import hashlib
import base64

class Player:
    def __init__(self, name,socket,pieces_per_player=None):
        self.name = name
        self.socket = socket
        self.hand = []
        self.playedHand=[]
        self.num_pieces = 0
        self.score = 0
        self.host=False
        self.pieces_per_player=pieces_per_player
        self.ready_to_play = False
        self.in_table = []
        self.deck = []
        self.nopiece = False
        self.keyMapDeck = dict()
        self.pickingPiece = False
        self.public_keys_list = [None] * 28
        self.nplayers = None
        self.previousPlayer = None

    def __str__(self):
        return str(self.toJson())

    def toJson(self):
        return {"name": self.name, "hand": self.hand, "score": self.score}

    def isHost(self):
        return self.host

    def pickPiece(self):
        if not self.ready_to_play and self.num_pieces==self.pieces_per_player:
            self.ready_to_play = True
        random.shuffle(self.deck)
        piece = self.deck.pop()
        self.insertInHand(piece)
        self.pickingPiece = True
        return {"action": "get_pieceInGame", "deck": self.deck, "piece" : piece}

    def updatePieces(self,i):
        self.num_pieces+=i

    def canPick(self):
        return self.num_pieces<self.pieces_per_player

    def insertInHand(self,piece):
        self.num_pieces += 1
        self.hand.append(piece)
        if self.num_pieces == self.pieces_per_player:
            self.ready_to_play = True
        #self.hand.sort(key=lambda p : int(p.values[0].value)+int(p.values[1].value))

    def removeFromHand(self):
        #self.num_pieces -= 1
        # baralha para tirar um peça random
        print(self.hand)
        random.shuffle(self.hand)
        hand_to_deck = self.hand.pop()
        # ordenar de volta
        #self.hand.sort(key=lambda p : int(p.values[0].value)+int(p.values[1].value))
        return hand_to_deck

    def checkifWin(self):
        print("Winner ",self.num_pieces == 0)
        return self.num_pieces == 0

    def encryptDeck(self, deck):
        new_deck = []
        for i in deck:
            c = SymCipher(''.join(random.choices(string.ascii_uppercase + string.digits, k=5)))

            key = c.getKey()
            #print("key: ", key)
            # encrypt tuple
            encrypt = c.cipher(encodeBase64(i))
            #print("str: ", encrypt)

            while encrypt in deck:
                print("AQUI")
                c = SymCipher(''.join(random.choices(string.ascii_uppercase + string.digits, k=5)))

                key = c.getKey()

                encrypt = c.cipher(encodeBase64(i))

            new_deck.append(encrypt)

            # guardar tuples e key
            self.keyMapDeck.update({encrypt: key})
        return new_deck

    def decipherHand(self, keys):
        tmp = []
        for tile in self.hand:
            if tile in keys.keys():
                key = keys[tile]
                plaintext = decodeBase64(SymCipher.decipherKey(tile, key))
                print("Peca: ", plaintext)
                tmp.append(plaintext)
        if len(tmp) > 0:
            self.hand = tmp

    def decipherPiece(self, key, peca):
        pieces = [p for p in self.hand if not isinstance(p,Piece)]
        if len(pieces) == 0:
            return None
        piece = pieces[0]
        print("ASDASD",piece)
        if peca == piece:
            print("TRUEEEEEEE", len(self.hand))
            self.hand.remove(piece)
            print("HAND",len(self.hand))
            newPiece = decodeBase64(SymCipher.decipherKey(piece, key))
            print("PECA::::",newPiece)
            self.hand.append(newPiece)
            return newPiece
        else:
            return None

    def find_piece_without_key(self):
        for i in range(len(self.hand)):
            if len(self.hand[i]) == 2:
                return i, self.hand[i][0]

    def check_added_piece(self):
        for i in self.hand:
            print("hand: ", self.hand)
            if len(i) == 2:
                return True
        return False

    def preparation(self):
        # mudar probabilidades
        decision = random.choices(['add', 'backoff'], weights=[1, 1], k=1)
        print(decision)

        if decision == ['add']:
            index_pecas, index_lista = self.find_piece_without_key()
            if index_pecas is not None:
                # gerar key pair
                asym = AsymCipher(1024)

                # guardar chave privada no tuple
                tp = self.hand[index_pecas]
                l = list(tp)
                l.append(asym.get_private_key())
                self.hand[index_pecas] = tuple(l)
                # print("pecas:", self.hand)

                # add chave publica à lista
                self.public_keys_list[index_lista] = asym.get_public_key()
                # print("publicas", self.public_keys_list)

        return self.public_keys_list

    def check_Cheating(self):
        if len(self.in_table) == 1:
            return False
        p0_e1 = self.in_table[0].values[1].value
        p1_e0 = self.in_table[1].values[0].value
        pU_e0 = self.in_table[len(self.in_table)-1].values[0].value
        pP_e1 = self.in_table[len(self.in_table)-2].values[1].value
        if p0_e1==p1_e0 and pU_e0==pP_e1:
            return False
        return True


    def play(self):
        res = {}
        if self.in_table == []:
            print("Empty table")
            piece = self.hand.pop()
            self.updatePieces(-1)
            self.playedHand.append(piece)
            res = {"action": "play_piece","piece":piece,"edge":0,"win":False}
        else:
            if not self.check_Cheating():
                edges = self.in_table[0].values[0].value, self.in_table[len(self.in_table) - 1].values[1].value
                print(str(edges[0])+" "+str(edges[1]))
                max = 0
                index = 0
                edge = None
                flip = False
                #get if possible the best piece to play and the correspondent assigned edge
                for i, piece in enumerate(self.hand):
                    aux = int(piece.values[0].value) + int(piece.values[1].value)
                    if aux > max:
                        if int(piece.values[0].value) == int(edges[0]):
                                max = aux
                                index = i
                                flip = True
                                edge = 0
                        elif int(piece.values[1].value) == int(edges[0]):
                                max = aux
                                index = i
                                flip = False
                                edge = 0
                        elif int(piece.values[0].value) == int(edges[1]):
                                max = aux
                                index = i
                                flip = False
                                edge = 1
                        elif int(piece.values[1].value) == int(edges[1]):
                                max = aux
                                index = i
                                flip = True
                                edge = 1
                #if there is a piece to play, remove the piece from the hand and check if the orientation is the correct
                if edge is not None:
                    piece = self.hand.pop(index)
                    self.playedHand.append(piece)
                    if flip:
                        piece.flip()
                    self.updatePieces(-1)
                    res = {"action": "play_piece", "piece": piece,"edge":edge,"win":self.checkifWin()}
                # if there is no piece to play try to pick a piece, if there is no piece to pick pass
                else:
                    input("VOU BUSCAR")
                    r = random.choices(['pick_piece', 'cheat'], weights=[5, 1], k=1)
                    if r == ['pick_piece']:
                        if len(self.deck)>0:
                            res = self.pickPiece()
                        else:
                            res = {"action": "pass_play", "piece": None, "edge": edge,"win":self.checkifWin()}
                    else:

                        cheat_piece = self.hand.pop()
                        cheat_edge = 0
                        self.playedHand.append(cheat_piece)
                        self.updatePieces(-1)
                        #input("FIZ BATOTA :P")
                        res = {"action": "play_piece", "piece": cheat_piece,"edge":cheat_edge,"win":self.checkifWin()}

                print("To play -> "+str(piece))
            else:
                #input("ALGUEM FEZ BATOTA!!")
                res = {"action": "cheat_detected", "cheater": self.previousPlayer}
        return res

class Piece:
    values = []

    def __init__(self, first, second):
        self.values = [SubPiece(first), SubPiece(second)]

    def __str__(self):
        return " {}:{}".format(str(self.values[0]),str(self.values[1]))

    def flip(self):
        self.values = [self.values[1], self.values[0]]

class SubPiece:
    value = None
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return "\033[1;9{}m{}\033[0m".format(int(self.value)+1, self.value)

class Deck:

    deck = []
    deckNormal = []
    hashKeys = dict()

    def __init__(self,pieces_per_player=5):
        with open('pieces', 'r') as file:
            pieces = file.read()
        indexes = random.sample(range(28),28)
        for piece in pieces.split(","):
            piece = piece.replace(" ", "").split("-")
            peca = Piece(piece[0], piece[1])
            if len(self.hashKeys.keys()) == 0:
                key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                print(key)
            else:
                key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                while key in self.hashKeys.values():
                    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                    print(key)

            dig = hmac.new(bytes(key, "utf-8"), msg=encodeBase64(peca), digestmod=hashlib.sha256).digest()
            res = base64.b64encode(dig).decode()
            index = indexes.pop()
            self.hashKeys[res] = index
            #self.deck.append((index, res))
            self.deck.append(Piece(piece[0], piece[1]))
            self.deckNormal.append((index, Piece(piece[0], piece[1])))

        #print("DECK: ",self.deck)
        #print("PSEUDO: ",self.psedoDeck)
        self.npieces = len(self.deck)
        print("NUMERO: ",self.npieces)
        self.pieces_per_player = pieces_per_player
        self.in_table = []

    def __str__(self):
        a = ""
        for piece in self.deck:
            a+=str(piece)
        return a

    def toJson(self):
        return {"npieces": self.npieces, "pieces_per_player": self.pieces_per_player, "in_table": self.in_table,"deck":self.deck}

