from deck_utils import *
import socket
import select
import sys
import queue
import pickle
from game import Game
import signal
import Colors
import time
import random
from security import diffieHellman,encodeBase64, decodeBase64
from security import SymCipher
from cc_utils import check_signature



# Main socket code from https://docs.python.org/3/howto/sockets.html
# Select with sockets from https://steelkiwi.com/blog/working-tcp-sockets/

class TableManager:

    def __init__(self, host, port,nplayers=4):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setblocking(False)  # non-blocking for select
        self.server.bind((host, port))  # binding to localhost on 50000
        self.server.listen()
        self.game = Game(nplayers)  # the game associated to this table manager
        self.nplayers=nplayers
        print("Nplayers = ",nplayers)
        #disconnecting players when CTRL + C is pressed
        signal.signal(signal.SIGINT, self.signal_handler)
        #signal.pause()
        self.sharedBase = 5
        self.dh_keys = {}
        self.players = {}
        self.pseudos=dict()
        self.allEncryptDeck = False

        print("Server is On")

        # configuration for select()
        self.inputs = [self.server]  # sockets where we read
        self.outputs = []  # sockets where we write

        self.message_queue = {}  # queue of messages

        while self.inputs:
            readable, writeable, exceptional = select.select(self.inputs, self.outputs, self.inputs)
            for sock in readable:
                if sock is self.server:  # this is our main socket and we are receiving a new client
                    connection, ip_address = sock.accept()
                    print(Colors.BRed+"A new client connected -> "+Colors.BGreen+"{}".format(ip_address)+Colors.Color_Off)
                    connection.setblocking(False)
                    self.inputs.append(connection)  # add client to our input list
                    self.message_queue[connection] = queue.Queue()

                else:  # We are receiving data from a client socket
                    data = sock.recv(100000)
                    if data:
                        to_send = self.handle_action(data, sock)
                        if to_send is not None:
                            self.message_queue[sock].put(to_send)  # add our response to the queue
                            if sock not in self.outputs:
                                self.outputs.append(sock)  # add this socket to the writeable sockets
                    else:
                        if sock in self.outputs:
                            self.outputs.remove(sock)
                        self.inputs.remove(sock)
                        sock.close()
                        del self.message_queue[sock]

            for sock in writeable:
                try:
                    to_send = self.message_queue[sock].get_nowait()
                except queue.Empty:  # Nothing more to send to this client
                    self.outputs.remove(sock)
                else:
                    sock.send(to_send)  # Send the info

            for sock in exceptional:  # if a socket is here, it has gone wrong and we must delete everything
                self.inputs.remove(sock)
                if sock in self.outputs:
                    self.outputs.remove(sock)
                sock.close()
                del self.message_queue[sock]

    def send_all(self, msg, socket=None):
        if socket is None:
            socket=self.server

        for sock in self.inputs:
            if sock is not self.server and sock is not socket :
                msgEncrypt = self.dh_keys[sock][2].cipher(encodeBase64(msg))
                #print("encruptALL: ", msgEncrypt)
                self.message_queue[sock].put(pickle.dumps(msgEncrypt))
                if sock not in self.outputs:
                    self.outputs.append(sock)
        time.sleep(0.1) #give server time to send all messages


    def send_host(self,msg):
        self.message_queue[self.game.host_sock].put(pickle.dumps(msg))
        if self.game.host_sock not in self.outputs:
            self.outputs.append(self.game.host_sock)

    def send_to_player(self,msg,sock):
        msgEncrypt = self.dh_keys[sock][2].cipher(encodeBase64(msg))
        self.message_queue[sock].put(pickle.dumps(msgEncrypt))
        if sock not in self.outputs:
            self.outputs.append(sock)

    def handle_action(self, data, sock):
        data = pickle.loads(data)
        print("DATA: ", data)

        if sock in self.dh_keys.keys():
            if len(self.dh_keys[sock]) == 3:
                data = decodeBase64(self.dh_keys[sock][2].decipher(data))
        print("MSG-->",data)
        action = data["action"]
        print("\n"+action)
        if data:
            if action == "TalkToPlayer":
                playerTo = data["to"]
                print("Sending message to ", playerTo)
                print(self.players[playerTo])
                self.send_to_player(data,self.players[playerTo])
                return None

            if action == "hello":
                privateNumber = random.randint(1, 16)
                keyToSend = diffieHellman(self.sharedBase,privateNumber)
                self.dh_keys[sock] = [privateNumber]
                msg = {"action": "login", "msg": "Welcome to the server, what will be your name?", "key":keyToSend}
                return pickle.dumps(msg)
            # TODO login mechanic is flawed, only nickname
            if action == "req_login":
                print("User {} requests login, with nickname {}".format(sock.getpeername(), data["msg"]))
                keyRecev = int(data["key"])
                sharedKey = diffieHellman(keyRecev, self.dh_keys[sock][0])
                print("SharedKey: ", sharedKey)
                self.dh_keys[sock].append(sharedKey)
                self.dh_keys[sock].append(SymCipher(str(sharedKey)))
                
                if not self.game.hasHost():  # There is no game for this tabla manager
                    self.game.addPlayer(data["msg"],sock,self.game.deck.pieces_per_player) # Adding host
                    self.players[data["msg"]] = sock
                    msg = {"action": "you_host", "msg": Colors.BRed+"You are the host of the game"+Colors.Color_Off}
                    print("msg: ", msg)
                    encrypt = self.dh_keys[sock][2].cipher(encodeBase64(msg))
                    print("User "+Colors.BBlue+"{}".format(data["msg"])+Colors.Color_Off+" has created a game, he is the first to join")
                    return pickle.dumps(encrypt)
                else:
                    if not self.game.hasPlayer(data["msg"]):
                        if self.game.isFull():
                            msg = {"action": "full", "msg": "This table is full"}
                            print("User {} tried to join a full game".format(data["msg"]))
                            return pickle.dumps(msg)
                        else:
                            self.game.addPlayer(data["msg"], sock,self.game.deck.pieces_per_player)  # Adding player
                            msg = {"action": "new_player", "msg": "New Player "+data["msg"]+" registered in game",
                                   "nplayers": self.game.nplayers, "game_players": self.game.max_players}
                            print("User "+Colors.BBlue+"{}".format(data["msg"])+Colors.Color_Off+" joined the game")
                            self.players[data["msg"]] = sock
                            #send info to all players
                            self.send_all(msg)

                            #check if table is full
                            if self.game.isFull():
                                print(Colors.BIPurple+"The game is Full"+Colors.Color_Off)
                                msg = {"action": "waiting_for_host", "msg": Colors.BRed+"Waiting for host to start the game"+Colors.Color_Off}
                                self.send_all(msg,sock)
                            msgEncrypt = self.dh_keys[sock][2].cipher(encodeBase64(msg))
                            return pickle.dumps(msgEncrypt)
                    else:
                        msg = {"action": "disconnect", "msg": "You are already in the game"}
                        print("User {} tried to join a game he was already in".format(data["msg"]))
                        msgEncrypt = self.dh_keys[sock][2].cipher(encodeBase64(msg))
                        return pickle.dumps(msgEncrypt)

            if action == "start_game":
                msg = {"action": "host_start_game", "msg": Colors.BYellow+"The Host started the game"+Colors.Color_Off}
                self.send_all(msg,sock)
                msgEncrypt = self.dh_keys[sock][2].cipher(encodeBase64(msg))
                return pickle.dumps(msgEncrypt)

            if action == "ready_to_play":
                msg = {"action": "host_start_game", "msg": Colors.BYellow+"The Host started the game"+Colors.Color_Off}
                self.send_all(msg,sock)
                msgEncrypt = self.dh_keys[sock][2].cipher(encodeBase64(msg))
                return pickle.dumps(msgEncrypt)

            if action == "get_game_propreties":
                msg = {"action": "rcv_game_propreties"}
                msg.update(self.game.toJson())
                msgEncrypt = self.dh_keys[sock][2].cipher(encodeBase64(msg))
                return pickle.dumps(msgEncrypt)

            player = self.game.currentPlayer()
            #check if the request is from a valid player
            if sock == player.socket:
                if action == "encryptDeck":
                    self.game.deck.deck = data["deck"]
                    print("NEW_DECK:::",self.game.deck.deck)
                    self.game.nextPlayer()
                    if self.game.allEncriptDeck:
                        self.game.next_action = "get_piece"

                    msg = {"action": "rcv_game_propreties"}
                    msg.update(self.game.toJson())
                    self.send_all(msg, sock)

                elif action == "get_piece":
                    self.game.deck.deck=data["deck"]
                    player.updatePieces(1)
                    if not self.game.started:
                        print("player pieces ", player.num_pieces)
                        print("ALL-> ", self.game.allPlayersWithPieces())
                        # if self.game.allPlayersWithPieces():
                        #     for a in range (0,self.nplayers):
                        #         p=self.game.nextPlayer()
                        #         print("DEBUG DARIO: ".join(map(str, self.player.hand)))

                        self.game.nextPlayer()
                        if self.game.allPlayersWithPieces():
                            self.game.started = True
                            self.game.next_action = "play"

                    msg = {"action": "rcv_game_propreties"}
                    msg.update(self.game.toJson())
                    self.send_all(msg,sock)

                elif action == "play_piece":
                    next_p = self.game.nextPlayer()
                    if data["piece"]is not None:
                        player.nopiece = False
                        player.updatePieces(-1)
                        if data["edge"]==0:
                            self.game.deck.in_table.insert(0,data["piece"])
                        else:
                            self.game.deck.in_table.insert(len(self.game.deck.in_table),data["piece"])

                    print("player pieces ",player.num_pieces)
                    print("player "+player.name+" played "+str(data["piece"]))
                    print("in table -> " + ' '.join(map(str, self.game.deck.in_table)) + "\n")
                    print("deck -> " + ' '.join(map(str, self.game.deck.deck)) + "\n")
                    if data["win"]:
                        if player.checkifWin():
                            print(Colors.BGreen+" WINNER "+player.name+Colors.Color_Off)
                            #msg = {"action": "end_game","winner":player.name}
                            choice=input("Save points? (blank/n")
                            if choice is "":
                                print("Reading card...")
                                serial=str(check_signature())
                                self.pseudos[serial]= player.name+"10"
                                print(self.pseudos[serial])

                            msg = {"action": "end_game", "winner": player.name}

                    else:
                        msg = {"action": "rcv_game_propreties"}
                    msg.update(self.game.toJson())
                    self.send_all(msg,sock)
                #no pieces to pick
                elif action == "pass_play":
                    self.game.nextPlayer()
                    #If the player passed the previous move
                    if player.nopiece:
                        print("No piece END")
                        msg = {"action": "end_game", "winner": Colors.BYellow+"TIE"+Colors.Color_Off}
                    #Update the variable nopiece so that the server can know if the player has passed the previous move
                    else:
                        print("No piece")
                        player.nopiece = True
                        msg = {"action": "rcv_game_propreties"}
                        msg.update(self.game.toJson())

                    self.send_all(msg, sock)
                    msgEncrypt = self.dh_keys[sock][2].cipher(encodeBase64(msg))
                    return pickle.dumps(msgEncrypt)
            else:
                msg = {"action": "wait","msg":Colors.BRed+"Not Your Turn"+Colors.Color_Off}
            msgEncrypt = self.dh_keys[sock][2].cipher(encodeBase64(msg))
            return pickle.dumps(msgEncrypt)

    #Function to handle CTRL + C Command disconnecting all players
    def signal_handler(self,sig, frame):
        print('You pressed Ctrl+C!')
        size = len(self.inputs)-1
        msg = {"action": "disconnect", "msg": "The server disconnected you"}
        i = 1
        for sock in self.inputs:
            if sock is not self.server:
                print("Disconnecting player " + str(i) + "/" + str(size))
                msgEncrypt = self.dh_keys[sock][2].cipher(encodeBase64(msg))
                sock.send(pickle.dumps(msgEncrypt))
                i+=1
        print("Disconnecting Server ")
        self.server.close()
        sys.exit(0)

try:
    NUM_PLAYERS = int(sys.argv[1])
except:
    NUM_PLAYERS = 3
a = TableManager('localhost', 50000,NUM_PLAYERS)
