from deck_utils import Piece
import random
import string
import hashlib
import hmac
import base64
import pickle
from security import encodeBase64, decodeBase64, SymCipher
import hmac
import hashlib
import base64



deck = []
new_deck = []
store = dict()


with open('pieces', 'r') as file:
    pieces = file.read()
indexes = random.sample(range(100), 28)
for piece in pieces.split(","):
    piece = piece.replace(" ", "").split("-")
    peca = Piece(piece[0], piece[1])
    deck.append(peca)

for i in deck:
    c = SymCipher(''.join(random.choices(string.ascii_uppercase + string.digits, k=5)))

    key = c.getKey()
    #print("key: ", key)
    # encrypt tuple
    encrypt = c.cipher(encodeBase64(i))
    #print("str: ", encrypt)

    while encrypt in new_deck:
        print("AQUI")
        c = SymCipher(''.join(random.choices(string.ascii_uppercase + string.digits, k=5)))

        key = c.getKey()

        encrypt = c.cipher(str(i))


    new_deck.append(encrypt)

    # guardar tuples e key
    store.update({encrypt: key})

    #TODO VER SE A KEY É UNICA OU NAO

deck2 = []
keys = dict()

for i in new_deck:
    c = SymCipher(''.join(random.choices(string.ascii_uppercase + string.digits, k=5)))

    key = c.getKey()
    #print("key: ", key)
    # encrypt tuple
    encrypt = c.cipher(encodeBase64(i))
    #print("str: ", encrypt)

    while encrypt in new_deck:
        print("AQUI")
        c = SymCipher(''.join(random.choices(string.ascii_uppercase + string.digits, k=5)))

        key = c.getKey()

        encrypt = c.cipher(str(i))


    deck2.append(encrypt)

    # guardar tuples e key
    keys.update({encrypt: key})

    #TODO VER SE A KEY É UNICA OU NAO

res = []

for i in deck2:

    key = keys[i]
    print("key: ", key)
    # encrypt tuple
    encrypt = decodeBase64(SymCipher.decipherKey(i,key))
    print("str: ", encrypt)
    res.append(encrypt)

deck2 = res

for i in deck2:

    key = store[i]
    print("key: ", key)
    # encrypt tuple
    encrypt = decodeBase64(SymCipher.decipherKey(i,key))
    print("str: ", encrypt)

