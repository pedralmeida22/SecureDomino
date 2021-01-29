import base64
import json
import pickle

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding as pd
from cryptography.hazmat.primitives import serialization
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
        return self.key

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
        return paddedText

    @staticmethod
    def decipherKey(msg, key):
        iv = msg[:16]
        cipherText = msg[16:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), default_backend())
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

        plaintext = decryptor.update(cipherText) + decryptor.finalize()
        paddedText = unpadder.update(plaintext) + unpadder.finalize()
        # print("p: ",paddedText)
        return paddedText


class AsymCipher:  # rsa
    def __init__(self, key_size=1024):
        self.priv_key = rsa.generate_private_key(65537, key_size, default_backend())

    def get_private_key(self):
        return self.priv_key

    def get_public_key(self):
        pem = self.priv_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem

    def cipher(self, msg):
        return self.get_public_key().encrypt(msg, pd.OAEP(pd.MGF1(hashes.SHA256()), hashes.SHA256(), None))

    def decipher(self, ciphertext):
        return self.get_private_key().decrypt(ciphertext, pd.OAEP(pd.MGF1(hashes.SHA256()), hashes.SHA256(), None))

    @staticmethod
    def cipherKey(msg, key):
        return key.encrypt(msg, pd.OAEP(pd.MGF1(hashes.SHA256()), hashes.SHA256(), None))

    @staticmethod
    def decipherKey(ciphertext,key):
        return key.decrypt(ciphertext, pd.OAEP(pd.MGF1(hashes.SHA256()), hashes.SHA256(), None))