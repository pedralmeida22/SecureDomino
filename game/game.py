from deck_utils import Deck,Player
from security import decodeBase64, SymCipher


class Game:
    def __init__(self,max_players):
        self.deck = Deck()
        self.completeDeck = []
        self.decipherDeck = []
        print("Deck created \n")
        self.public_keys_list = [None] * 28
        self.max_players = max_players
        self.nplayers = 0
        self.players = []
        self.player_index = 0
        self.init_distribution = True
        self.next_action="encryptDeck"  #"get_piece"
        self.started = False
        self.all_ready_to_play = False
        self.allEncriptDeck = False
        self.allSendKeys = False


    def checkDeadLock(self):
        return all([ player.nopiece for player in self.players ])

    def allPlayersWithPieces(self):
        return all([p.num_pieces == p.pieces_per_player for p in self.players])

    def currentPlayer(self):
        return self.players[self.player_index]

    def nextPlayer(self):
        self.player_index +=1
        if self.player_index == self.max_players:
            self.allEncriptDeck = True
            self.player_index = 0
        return self.players[self.player_index]

    def previousPlayer(self):
        self.player_index -= 1
        if self.player_index < 0:
            self.allSendKeys = True
            self.player_index = 0
        return self.players[self.player_index]

    def addPlayer(self,name,socket,pieces):
        self.nplayers+=1
        assert  self.max_players>=self.nplayers
        player = Player(name,socket,pieces)
        print(player)
        self.players.append(player)

    def hasHost(self):
        return len(self.players)>0

    def hasPlayer(self,name):
        for player in self.players:
            if name == player.name:
                return True
        return False

    def isFull(self):
        return self.nplayers == self.max_players

    def toJson(self):
        msg = {"next_player":self.players[self.player_index].name ,"nplayers":self.nplayers
            ,"next_action":self.next_action}
        msg.update(self.deck.toJson())
        return msg

    def decipherCompleteDeck(self, keys):
        tmp = []
        for tile in self.completeDeck:
            if tile in keys.keys():
                key = keys[tile]
                plaintext = decodeBase64(SymCipher.decipherKey(tile, key))
                print("PECA: ", plaintext)
                tmp.append(plaintext)
        if len(tmp) > 0:
            self.completeDeck = tmp + self.deck.deck    #adiciona as que não estao nas hands

    def decipherPiece(self,piece, key):
        index = self.completeDeck.index(piece)
        oldPiece = self.completeDeck.pop(index)
        newPiece = decodeBase64(SymCipher.decipherKey(oldPiece,key))
        print("PECA::::",newPiece)
        self.completeDeck.append(newPiece)
        return newPiece

    def check_added_to_public_list(self):
        count = 0
        print("pu list: ", self.public_keys_list)
        for i in self.public_keys_list:
            if i is None:
                count += 1
        print("count: ", count)
        print("n pecas: ", self.players[0].pieces_per_player)
        # n nones expected = total de peças - num_players * num_pecas_player
        if count == 28 - self.nplayers * self.players[0].pieces_per_player:
            return True
        return False
