import base64
import random
import string
from security import encodeBase64, SymCipher, decodeBase64, AsymCipher
import hmac
import hashlib
import base64
import pickle


from security import encodeBase64

class bitCommit():

    def __init__(self, float1, float2, tiles):
        self.float1 = float1
        self.float2 = float2
        self.tiles = tiles
        self.newTiles = ""

    def value(self):
        for a in self.tiles:
            self.newTiles += str(a)
        print("HASHING:")
        print(self.float1)
        print(self.float2)
        print("WITH TILES:")
        print(self.tiles)

        key=self.float1*self.float2

        a=hmac.new(bytes(str(key), "utf-8"), msg=encodeBase64(self.tiles), digestmod=hashlib.sha256).digest()
        res = base64.b64encode(a).decode()
        self.value=res
        return self.value

