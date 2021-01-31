import os

def adicionarPontos(num, valor):
    fA=open("points.txt", "r", encoding="utf-8")
    texto=fA.read()

    if texto == "":
        fW=open("points.txt", "a", encoding="utf-8")
        fW.write(str(num)+" -- " +str(valor))

    
    else:
        fW=open("points.txt","w",encoding="utf-8")

        ar=texto.split("\n")
        pontos=dict()
        for a in ar:
            linha=a.split(" -- ")
            pontos[linha[0]]=linha[1]

        try:
            pont = int(pontos[str(num)])
            novos=pont+valor
            pontos[str(num)]=novos
        except:
            pontos[str]=valor
        
        for key, value in pontos.items():
            fW.write(str(key)+" -- "+str(value)+"\n")


def main():
    adicionarPontos(123, 124)

    
main()