from deck_utils import Piece
import random
import string
import hashlib
import hmac
import base64
import pickle
from security import encodeBase64, decodeBase64
import hmac
import hashlib
import base64



deckSecure = []
hashKeys = dict()


with open('pieces', 'r') as file:
    pieces = file.read()
indexes = random.sample(range(100), 28)
for piece in pieces.split(","):
    piece = piece.replace(" ", "").split("-")
    peca = Piece(piece[0], piece[1])
    if len(hashKeys.keys()) == 0:
        key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        print(key)
    else:
        key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        while key in hashKeys.values():
            key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            print(key)

    dig = hmac.new(bytes(key, "utf-8"), msg=encodeBase64(peca), digestmod=hashlib.sha256).digest()
    res = base64.b64encode(dig).decode()
    index = indexes.pop()
    hashKeys[index] = key
    deckSecure.append((index, res))

print(deckSecure)