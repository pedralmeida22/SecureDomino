import socket
import sys
import pickle
import random
import Colors
import string
from deck_utils import Player, Piece
import random
from security import diffieHellman, encodeBase64, decodeBase64
from security import SymCipher
from cc_utils import getSerial


class client():

    def __init__(self, host, port):
        self.dh_keys = {}
        self.sharedBase = 5
        self.sharedBaseClients = 7
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.connect((host, port))
        first_msg = {"action": "hello"}
        self.sock.send(pickle.dumps(first_msg))
        self.player = None
        self.receiveData()
        self.randomB1 = 0
        self.randomB2 = 0
        self.bitCom = 0

    def receiveData(self):
        while True:
            data = self.sock.recv(1000000)
            if data:
                self.handle_data(data)

    def handle_data(self, data):
        data = pickle.loads(data)
        #print("DATA: ", data)
        print("")
        if "server" in self.dh_keys:
            data = decodeBase64(self.dh_keys['server'][2].decipher(data))
        action = data["action"]
        #print(data)
        print("\n" + action)
        if action == "KeyToPiecePlayer":
            key = data["key"]
            print("KEYTOPIECE",data["piece"])
            piece = self.player.decipherPiece(key,data["piece"])
            if isinstance(piece,Piece):
                self.player.pickingPiece = False
                msg = {"action": "get_piece", "deck": self.player.deck}
                msgEncrypt = self.dh_keys['server'][2].cipher(encodeBase64(msg))
                self.sock.send(pickle.dumps(msgEncrypt))

        if action == "whatIsThisPiece":
            #print("PECA;;;;",data["piece"])
            if data["piece"] in self.player.keyMapDeck.keys():
                print("TRUEEEEEEEEEEE")
                msg = {"action": "KeyToPiece", "key": self.player.keyMapDeck[data["piece"]], "piece": data["piece"]}
                if self.player.pickingPiece:
                    print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA1111111")
                    piece = self.player.decipherPiece(self.player.keyMapDeck[data["piece"]], data["piece"])
                    msg.update({"sendKey" : False})
                    if isinstance(piece, Piece):
                        self.player.pickingPiece = False
                        msg = {"action": "get_piece", "deck": self.player.deck, "key": self.player.keyMapDeck[data["piece"]], "piece": data["piece"]}

                msgEncrypt = self.dh_keys['server'][2].cipher(encodeBase64(msg))
                self.sock.send(pickle.dumps(msgEncrypt))
                print("DONE")

        if action == "login":
            nickname = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # input(data["msg"])
            print("Your name is " + Colors.BBlue + nickname + Colors.Color_Off)
            print("keyRecive", data["key"])
            # diffieHellman
            privateNumber = random.randint(1, 16)
            keyToSend = diffieHellman(self.sharedBase, privateNumber)
            sharedKey = diffieHellman(int(data["key"]), privateNumber)
            self.dh_keys['server'] = [privateNumber, sharedKey, SymCipher(str(sharedKey))]
            print("SharedKey: ", sharedKey)
            msg = {"action": "req_login", "msg": nickname, "key": keyToSend}
            self.player = Player(nickname, self.sock)
            self.sock.send(pickle.dumps(msg))
            return
            # todo login
        elif action == "you_host":
            self.player.host = True
        elif action == "new_player":
            print(data["msg"])
            nome = data["msg"].split(" ")[2]
            # diffieHellman
            privateNumber = random.randint(1, 16)
            keyToSend = diffieHellman(self.sharedBase, privateNumber)

            self.dh_keys[nome] = [privateNumber]

            msg = {"action": "TalkToPlayer", "actionPlayer": "openSession", "msg": "Hello", "key": keyToSend,
                   "from": self.player.name, "to": nome}
            msgEncrypt = self.dh_keys['server'][2].cipher(encodeBase64(msg))
            self.sock.send(pickle.dumps(msgEncrypt))
            print("There are " + str(data["nplayers"]) + "\\" + str(data["game_players"]))

        elif action == "waiting_for_host":
            if self.player.host:
                input(Colors.BGreen + "PRESS ENTER TO START THE GAME" + Colors.Color_Off)
                msg = {"action": "start_game"}
                msgEncrypt = self.dh_keys['server'][2].cipher(encodeBase64(msg))
                self.sock.send(pickle.dumps(msgEncrypt))
                print("Sent ", msg)
            else:
                print(data["msg"])

        elif action == "TalkToPlayer":
            #print("DATA_PlayerAntes:", data)
            player = data["from"]  # quem mandou a mensagem
            if data["from"] in self.dh_keys.keys():
                if len(self.dh_keys[data["from"]]) == 3:
                    data = decodeBase64(self.dh_keys[data["from"]][2].decipher(data["msg"]))
            print("DATA_Player:", data)
            actionPlayer = data["actionPlayer"]

            if actionPlayer == "openSession":

                if player not in self.dh_keys.keys():
                    # diffieHellman
                    privateNumber = random.randint(1, 16)
                    keyToSend = diffieHellman(self.sharedBase, privateNumber)
                    keyRecevied = int(data["key"])
                    print("Key recebida: ", keyRecevied)
                    sharedKey = diffieHellman(keyRecevied, privateNumber)
                    self.dh_keys[player] = [privateNumber, sharedKey, SymCipher(str(sharedKey))]
                    msg = {"action": "TalkToPlayer", "actionPlayer": "openSession", "msg": "Hello", "key": keyToSend,
                           "from": self.player.name, "to": player}
                    msgEncrypt = self.dh_keys['server'][2].cipher(encodeBase64(msg))
                    self.sock.send(pickle.dumps(msgEncrypt))
                else:
                    keyRecevied = int(data["key"])
                    print("Key recebida: ", keyRecevied)
                    sharedKey = diffieHellman(keyRecevied, self.dh_keys[player][0])
                    self.dh_keys[player].append(sharedKey)
                    self.dh_keys[player].append(SymCipher(str(sharedKey)))
                    msgToPlayer = {"actionPlayer": "SessionEstabelicida", "msg": "WE GUICCI"}
                    msgToPlayerEncrypt = self.dh_keys[player][2].cipher(encodeBase64(msgToPlayer))
                    msg = {"action": "TalkToPlayer", "msg": msgToPlayerEncrypt, "from": self.player.name, "to": player}
                    msgEncrypt = self.dh_keys['server'][2].cipher(encodeBase64(msg))
                    self.sock.send(pickle.dumps(msgEncrypt))

            if actionPlayer == "SessionEstabelicida":
                print("Sessao Estabecida com ", player)


        elif action == "host_start_game":
            print(data["msg"])
            msg = {"action": "get_game_propreties"}
            msgEncrypt = self.dh_keys['server'][2].cipher(encodeBase64(msg))
            self.sock.send(pickle.dumps(msgEncrypt))
            print("Sent ", msg)

        elif action == "rcv_game_propreties":
            self.player.nplayers = data["nplayers"]
            self.player.npieces = data["npieces"]
            self.player.pieces_per_player = data["pieces_per_player"]
            self.player.in_table = data["in_table"]
            self.player.deck = data["deck"]
            player_name = data["next_player"]
            if "teste" in data.keys():
                print("#############",data["teste"])
            if data["next_player"] == self.player.name:
                player_name = Colors.BRed + "YOU" + Colors.Color_Off
            #print("deck -> " + ' '.join(map(str, self.player.deck)) + "\n")
            #print("hand -> " + ' '.join(map(str, self.player.hand)))

            if len(self.player.hand) is 5:
                #print(set(self.player.hand))
                #print("playedHand -> " + ' '.join(map(str, self.player.playedHand)))

                self.randomB1 = random.random()
                self.randomB2 = random.random()
                orderedTiles = set(self.player.hand)
                a = hash(self.randomB1)
                b = hash(self.randomB2)
                c = orderedTiles.__hash__
                self.bitCom = str(a) + str(b) + str(c)
                # hash((self.randomB1, self.randomB2, orderedTiles))
                makePublic = (self.randomB1, self.bitCom)

            print("in table -> " + ' '.join(map(str, data["in_table"])) + "\n")
            print("Current player ->", player_name)
            print("next Action ->", data["next_action"])


            if "keys" in data.keys():
                self.player.decipherHand(data["keys"])

            if self.player.name == data["next_player"]:

                if data["next_action"] == "encryptDeck":
                    new_deck = self.player.encryptDeck(data["deck"])
                    random.shuffle(new_deck)                            #reordena o baralho
                    #print("NEW_DECK:::", new_deck)
                    msg = {"action": "encryptDeck", "deck": new_deck}
                    msgEncrypt = self.dh_keys['server'][2].cipher(encodeBase64(msg))
                    self.sock.send(pickle.dumps(msgEncrypt))

                if data["next_action"] == "get_piece":
                    print("AHSIDAPBÇDASKJD\n\n\n")
                    #input("STOP")
                    if not self.player.ready_to_play:
                        # r = random.choices(['pickup', 'backoff'], weights=[5, 95], k=1)
                        # print(r)
                        # # input("enter:")
                        # # pickup
                        # if r == ['pickup']:
                        #     print("pickup\n\n\n")
                        #     #random.shuffle(self.player.deck)
                        #     piece = self.player.deck.pop()
                        #     print("PLAYERPICK-->",len(self.player.deck))
                        #     self.player.insertInHand(piece)
                        #
                        # # "back off"
                        # else:
                        #     r2 = random.choices(['switch', 'backoff'], weights=[1, 1], k=1)
                        #     print(r2)
                        #     # input("enter:")
                        #     # trocar pecas
                        #     if r2 == ['switch']:
                        #         print("switch\n\n\n")
                        #         # tirar um peça do deck
                        #         #random.shuxffle(self.player.deck)
                        #         piece = self.player.deck.pop()
                        #         self.player.insertInHand(piece)
                        #         print(self.player.hand)
                        #         # devolver uma peça ao deck
                        #         hand_to_deck = self.player.removeFromHand()
                        #         self.player.deck.append(hand_to_deck)
                        #
                        #     else:  # truly back off
                        #         print("Nadaaa\n\n\n")
                        #random.shuffle(self.player.deck)
                        piece = self.player.deck.pop()
                        self.player.insertInHand(piece)
                        msg = {"action": "get_piece", "deck": self.player.deck}
                        msgEncrypt = self.dh_keys['server'][2].cipher(encodeBase64(msg))
                        self.sock.send(pickle.dumps(msgEncrypt))

                if data["next_action"] == "revelationStage":
                    print("CompleteDeck--->", len(data["completeDeck"]))
                    print("hand -> " + ' '.join(map(str, self.player.hand)))
                    #print("Deck--->", len(data["deck"]))

                    tilesInHands = [tile for tile in data["completeDeck"] if tile not in data["deck"]]
                    print("tilesHands--->", len(tilesInHands))

                    keys = {encrypt: key for (encrypt, key) in self.player.keyMapDeck.items() if encrypt in tilesInHands}
                    #print("Keys --->", keys)
                    self.player.decipherHand(keys)
                    #input("Press ENter \n\n")
                    msg = {"action": "revelationStage", "keys": keys}
                    msgEncrypt = self.dh_keys['server'][2].cipher(encodeBase64(msg))
                    self.sock.send(pickle.dumps(msgEncrypt))


                if data["next_action"] == "play":
                    print("MAO--->",self.player.hand)
                    #input("Enter\n\n\n")
                    # input(Colors.BGreen+"Press ENter \n\n"+Colors.Color_Off)
                    #print("HAND----->",self.player.hand)
                    msg = self.player.play()
                    msgEncrypt = self.dh_keys['server'][2].cipher(encodeBase64(msg))
                    self.sock.send(pickle.dumps(msgEncrypt))

        elif action == "end_game":
            winner = data["winner"]

            orderedPlayed = self.player.playedHand
            a = hash(self.randomB1)
            b = hash(self.randomB2)
            c = orderedPlayed
            ver = str(a) + str(b) + str(c.__hash__)
            if ver == self.bitCom:
                print("NÃO FEZ BATOTA")
            else:
                print("KICK")

            if data["winner"] == self.player.name:
                winner = Colors.BRed + "YOU" + Colors.Color_Off
                choice = input("Save points? (blank/n")
                if choice is "":
                    print("Reading card...")
                    serial = getSerial()
                    msg = {"action": "reg_points", "msg": serial}
                    msgEncrypt = self.dh_keys['server'][2].cipher(encodeBase64(msg))
                    self.sock.send(pickle.dumps(msgEncrypt))
            else:
                winner = Colors.BBlue + winner + Colors.Color_Off
            print(Colors.BGreen + "End GAME, THE WINNER IS: " + winner)


        elif action == "wait":
            print(data["msg"])

        elif action == "disconnect":
            self.sock.close()
            print("PRESS ANY KEY TO EXIT ")
            sys.exit(0)


a = client('localhost', 50000)
