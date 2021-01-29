from security import *
import random
from cryptography.hazmat.primitives import serialization
from deck_utils import Piece


# fase 6
# peças do jogador -> lista de tuplos (index, P(i))
pecas1 = [(0, "a"), (3, "b"), (5, "c")]

# lista de chaves publicas random em que cada jogador preenche a posiçao i dessa lista consoante
# o index das peças que têm
l_pubs = [None] * 10

# ver num de Nones na lista com base no num de jogadores
# mandar lista para outro player


def do():
    # mudar probabilidades
    decision = random.choices(['add', 'backoff'], weights=[1, 1], k=1)
    print(decision)

    if decision == ['add']:
        index_pecas, index_lista = find_piece_without_key()
        if index_pecas is not None:
            # gerar key pair
            asym = AsymCipher(1024)

            # guardar chave privada no tuple
            tp = pecas1[index_pecas]
            l = list(tp)
            l.append(asym.get_private_key())
            pecas1[index_pecas] = tuple(l)
            print("pecas:", pecas1)

            # add chave publica à lista
            l_pubs[index_lista] = asym.get_public_key()
            print("publicas", l_pubs)

def reverse():
    for p in l_pubs:
        if p is not None:
            print(serialization.load_pem_public_key(p,default_backend()))

# retorna index do tuple e da peca
def find_piece_without_key():
    for i in range(len(pecas1)):
        if len(pecas1[i]) == 2:
            return i, pecas1[i][0]


def check():
    for i in pecas1:
        if len(i) == 2:
            return True
    return False


def check2():
    count = 0
    for i in l_pubs:
        if i is None:
            count += 1
    # n nones expected = total de peças - num_players * num_pecas_player
    if count > 10 - 1 * 3:
        return True
    return False


def main():
    while check2() and check():
        do()
    reverse()


main()
p = Piece(5,5)

plaintext = ("oi seguranca, domino seguro",p.values[0].value,p.values[1].value)
print(plaintext)

asym = AsymCipher(1024)
key = asym.get_public_key()


ciphertext = asym.cipher(pickle.dumps(plaintext),serialization.load_pem_public_key(key,default_backend()))
print("cipher: ", ciphertext)

plaintext = asym.decipher(ciphertext)
print("plain: ", pickle.loads(plaintext))

