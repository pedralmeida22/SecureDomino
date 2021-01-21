from PyKCS11 import *
from PyKCS11.LowLevel import *
import os
import platform
import random
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.hazmat.primitives.asymmetric import (padding, rsa, utils)
from cryptography.hazmat.backends import default_backend
from security import encodeBase64, SymCipher

def getLib():
    if platform.system() is "Windows":
        lib = "pteidpkcs11.dll"
    else:
        lib = "libpteidpkcs11.so"

    return lib

def check_signature():
    lib=getLib()
    pkcs11 = PyKCS11.PyKCS11Lib()
    pkcs11.load(lib)
    slots = pkcs11.getSlotList()

    for slot in slots:
        if 'CARTAO DE CIDADAO ' in pkcs11.getTokenInfo(slot).label:
            data = bytes('data to be signed ', 'utf-8')
            session = pkcs11.openSession(slot)
            privKey = session.findObjects([(CKA_CLASS, CKO_PRIVATE_KEY), (CKA_LABEL, 'CITIZEN AUTHENTICATION KEY')])[0]
            # session.getAttributeValue(privKey, [], True)[0]

            objects = session.findObjects()

            signature = bytes(session.sign(privKey, data, Mechanism(CKM_SHA1_RSA_PKCS)))
            session.closeSession
            # session = pkcs11.openSession(slot)
            pubKeyHandle = session.findObjects([(CKA_CLASS, CKO_PUBLIC_KEY), (CKA_LABEL, 'CITIZEN AUTHENTICATION KEY')])[0]
            pubKeyDer = session.getAttributeValue(pubKeyHandle, [CKA_VALUE], True)[0]
            session.closeSession
            pubKey = load_der_public_key(bytes(pubKeyDer), default_backend())
            try:
                pubKey.verify(signature, data, padding.PKCS1v15(), hashes.SHA1())
                print(' Verification succeeded.')
                print("É NO FOR")
                for obj in objects:
                    l = session.getAttributeValue(obj, [CKA_LABEL])[0]
                    if l == 'CITIZEN SIGNATURE CERTIFICATE':
                        print("Serial: ")
                        print(session.getAttributeValue(obj, [CKA_SERIAL_NUMBER], True)[0])
                        return (session.getAttributeValue(obj, [CKA_SERIAL_NUMBER], True)[0])

            except:
                print(' Verification failed ')


def getSerial():
    lib=getLib()
    pkcs11 = PyKCS11.PyKCS11Lib()
    pkcs11.load(lib)
    slots = pkcs11.getSlotList()
    for slot in slots:
        if 'CARTAO DE CIDADAO ' in pkcs11.getTokenInfo(slot).label:
            session = pkcs11.openSession(slot)
            objects = session.findObjects()

            for obj in objects:
                l = session.getAttributeValue(obj, [CKA_LABEL])[0]
                if l == 'CITIZEN SIGNATURE CERTIFICATE':
                    print("Serial: ")
                    try:
                        serial=session.getAttributeValue(obj, [CKA_SERIAL_NUMBER], True)[0]
                        session.closeSession

                        sym=SymCipher("cc")
                        res=sym.cipher(encodeBase64(serial))

                        print(res)
                        return res
                    except Exception as ex:
                        print(' Verification failed: ')
                        print(ex)


def info_card():
    lib=getLib()
    pkcs11 = PyKCS11.PyKCS11Lib()
    pkcs11.load(lib)
    slots = pkcs11.getSlotList()
    for slot in slots:
        print(pkcs11.getTokenInfo(slot))


def encryptPK(objeto):
    lib=getLib()
    pkcs11 = PyKCS11.PyKCS11Lib()
    pkcs11.load(lib)
    slots = pkcs11.getSlotList()
    for slot in slots:
        if 'CARTAO DE CIDADAO ' in pkcs11.getTokenInfo(slot).label:
            data = bytes(objeto)
            session = pkcs11.openSession(slot)
            privKey = session.findObjects([(CKA_CLASS, CKO_PRIVATE_KEY), (CKA_LABEL, 'CITIZEN AUTHENTICATION KEY')])[0]
            # session.getAttributeValue(privKey, [], True)[0]
            objects = session.findObjects()

            #signature = bytes(session.sign(privKey, data, Mechanism(CKM_SHA1_RSA_PKCS)))
            signature = session.encrypt(priv_key, data, Mechanism(CKM_SHA1_RSA_PKCS))

    return signature


def decrypt(objeto):
    lib=getLib()
    pkcs11 = PyKCS11.PyKCS11Lib()
    pkcs11.load(lib)
    slots = pkcs11.getSlotList()
    for slot in slots:
        if 'CARTAO DE CIDADAO ' in pkcs11.getTokenInfo(slot).label:
            session = pkcs11.openSession(slot)

            pubKeyHandle = session.findObjects([(CKA_CLASS, CKO_PUBLIC_KEY), (CKA_LABEL, 'CITIZEN AUTHENTICATION KEY')])[0]
            pubKeyDer = session.getAttributeValue(pubKeyHandle, [CKA_VALUE], True)[0]
            session.closeSession
            pubKey = load_der_public_key(bytes(pubKeyDer), default_backend())
            try:
                pubKey.verify(objeto, data, padding.PKCS1v15(), hashes.SHA1())
                print(' Verification succeeded.')
                for obj in objects:
                    l = session.getAttributeValue(obj, [CKA_LABEL])[0]
                    if l == 'CITIZEN SIGNATURE CERTIFICATE':
                        print("Serial: ")
                        print(session.getAttributeValue(obj, [CKA_SERIAL_NUMBER], True)[0])
                        return (session.getAttributeValue(obj, [CKA_SERIAL_NUMBER], True)[0])

            except:
                print(' Verification failed ')
