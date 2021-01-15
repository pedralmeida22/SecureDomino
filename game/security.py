import base64
import json
import pickle

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher , algorithms , modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os

def diffieHellman(base,expoente):
    sharePrime = 23
    return (base ** expoente) % sharePrime

def encodeBase64(data):
    #return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
    return base64.b64encode(pickle.dumps(data))
def decodeBase64(data):
    #return json.loads(base64.urlsafe_b64decode(data).decode())
    return pickle.loads(base64.b64decode(data))

class SymCipher:
    def __init__(self, pwd):
        self.pwd = pwd
        self.generateKey()

    def getKey(self):
        self.key

    def generateKey(self):
        salt = b'r\00'
        kdf = PBKDF2HMAC(hashes.SHA1(), 16, salt, 1000, default_backend())
        self.key = kdf.derive(bytes(self.pwd, "UTF-8"))


    def cipher(self,msg):
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()

        if not isinstance(msg,bytes):
            msg = bytes(msg, "UTF-8")

        padded = padder.update(msg) + padder.finalize()
        cipherText = encryptor.update(padded) + encryptor.finalize()

        return iv+cipherText


    def decipher(self, msg):
        iv = msg[:16]
        cipherText = msg[16:]



        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), default_backend())
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

        plaintext = decryptor.update(cipherText) + decryptor.finalize()
        paddedText = unpadder.update(plaintext) + unpadder.finalize()
        #print("p: ",paddedText)
        return plaintext

