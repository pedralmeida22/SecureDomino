from security import *
import random
import string

from game.security import decodeBase64, encodeBase64, SymCipher

deck = [(1, 'p1'), (1, 'p1'), (3, 'p3')]
test = [1,1,1,1,4,5,5,5,6]
new_deck = []
store = dict()

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

for i in new_deck:

    key = store[i]
    print("key: ", key)
    # encrypt tuple
    encrypt = decodeBase64(SymCipher.decipherKey(i,key))
    print("str: ", encrypt)


# shuffle
random.shuffle(new_deck)
print(new_deck)
print("DICT:::",store)
