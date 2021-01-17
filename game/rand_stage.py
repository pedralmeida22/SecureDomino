from security import *
import random

deck = [(1, 'p1'), (2, 'p2'), (3, 'p3')]
new_deck = []
store = dict()

for i in deck:
    c = SymCipher('blabla')

    key = c.getKey()
    # print("key: ", key)

    # encrypt tuple
    encrypt = c.cipher(str(i))
    # print("str: ", encrypt)

    new_deck.append(encrypt)

    # guardar tuples e key
    store.update({encrypt: key})

# shuffle
random.shuffle(new_deck)
print(new_deck)
