
import json
import os
import time

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_PONTOS = "pontos.json"


def carregar_dados():
    usuarios = []
    saldo_pontos = 0

    if os.path.exists(ARQUIVO_USUARIOS):
        with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as arquivo:
            try:
                usuarios = json.load(arquivo)
            except json.JSONDecodeError:
                usuarios = []

    if os.path.exists(ARQUIVO_PONTOS):
        with open(ARQUIVO_PONTOS, "r", encoding="utf-8") as arquivo:
            try:
                dados = json.load(arquivo)
                saldo_pontos = dados.get("saldo_pontos", 0)
            except json.JSONDecodeError:
                saldo_pontos = 0

    return usuarios, saldo_pontos


def salvar_usuarios():
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as arquivo:
        json.dump(usuarios, arquivo, ensure_ascii=False, indent=4)


def salvar_pontos():
    with open(ARQUIVO_PONTOS, "w", encoding="utf-8") as arquivo:
        json.dump({"saldo_pontos": saldo_pontos}, arquivo, ensure_ascii=False, indent=4)


usuarios, saldo_pontos = carregar_dados()


def cadastrar_usuario():
    print("\n----- CADASTRO DE USUÁRIO -----")

    nome = input("Digite seu nome: ").strip()

    while nome == "":
        nome = input("Nome inválido. Digite novamente: ").strip()

    email = input("Digite seu e-mail: ").strip()

    while "@" not in email or "." not in email:
        email = input("E-mail inválido. Digite novamente: ").strip()

    for usuario in usuarios:
        if usuario["email"] == email:
            print("Já existe um usuário com este e-mail.")
            return

    senha = input("Digite sua senha: ").strip()

    while len(senha) < 4:
        senha = input("Senha inválida. Digite novamente: ").strip()

    usuario = {
        "nome": nome,
        "email": email,
        "senha": senha
    }

    usuarios.append(usuario)
    salvar_usuarios()

    print(f"\nUsuário {nome} cadastrado com sucesso!")

    def login():
        print ("\n----- LOGIN -----")

    email = input("Digite seu e-mail: ").strip()
    senha = input("Digite sua senha: ").strip()

    for usuario in usuarios:
        if usuario["email"] == email and usuario["senha"] == senha:
            print(f"\nBem-vindo, {usuario['nome']}!")
            time.sleep(1)
            return True

    print("\nE-mail ou senha incorretos.")
    time.sleep(1.5)
    return False

def validar_atividade():
    global saldo_pontos

    print("\n----- VALIDAR ATIVIDADE -----")

    comprovante = input("Informe o comprovante: ").strip()

    if comprovante == "":
        print("Comprovante inválido.")
        return

    print("IA analisando comprovante...\n")
    time.sleep(2)
    print("Comprovante aprovado!\n")

    saldo_pontos += 50

    salvar_pontos()
    time.sleep(1.5)
    print("Você ganhou 50 pontos!\n")
    print(f"Saldo atual: {saldo_pontos} pontos.")


def visualizar_pontos():
    print("\n----- SALDO DE PONTOS -----")
    print(f"Você possui {saldo_pontos} pontos.")


def converter_pontos():
    global saldo_pontos

    print("\n----- CONVERTER PONTOS -----")

    if saldo_pontos < 100:
        print("Pontos insuficientes.")
        return

    saldo_pontos -= 100

    salvar_pontos()

    print("Passagem gerada com sucesso!")
    print(f"Saldo restante: {saldo_pontos} pontos.")


def chatbot():
    print("\n----- Rottinha CHATBOT -----")

    pergunta = input("Digite sua dúvida: ").strip()

    if pergunta:
        print("Sua solicitação foi registrada.")
    else:
        print("Nenhuma pergunta informada.")


def desativar_conta():
    print("\n----- EXCLUIR USUÁRIO -----")

    email = input("Digite o e-mail do usuário: ").strip()

    for usuario in usuarios:
        if usuario["email"] == email:
            usuarios.remove(usuario)
            salvar_usuarios()
            print("Conta excluida com sucesso.")
            return

    print("Email não encontrado.")

def gerar_qrcode():
    global saldo_pontos

    print("\n----- GERAR QR CODE -----")

    if saldo_pontos < 150:
        print("Você precisa de 150 pontos para gerar o QR Code.")
        print(f"Saldo atual: {saldo_pontos} pontos.")
        return

    saldo_pontos -= 150

    salvar_pontos()

    qr_code = """
█████████████████████████
██ ▄▄▄▄▄ ██▀▄█ ▄▄▄▄▄ ████
██ █   █ █ ▀ █ █   █ ████
██ █▄▄▄█ █▄▀▄█ █▄▄▄█ ████
██▄▄▄▄▄▄▄█▄█▄█▄▄▄▄▄▄▄████
██ ▄▀▄ ▄▀█ ▄█ ▄ ▄▀█▄ ████
██▄█▀▄▄▄█▄▀▀▀▄█▄▄▀██▄████
██ ▄▄▄▄▄ █▄ ▄ ▄█▀▄▀▄█████
██ █   █ █▀█▄▄▀▀▄▀█▄█████
██ █▄▄▄█ █ ▄▀█▄▀▀█▄█ ████
██▄▄▄▄▄▄▄█▄▄▄██▄█▄▄▄█████
█████████████████████████
"""

    print("\nQR CODE GERADO COM SUCESSO!")
    print(qr_code)

    print("150 pontos foram utilizados.")
    print(f"Saldo restante: {saldo_pontos} pontos.")


def menu():
    while True:
        print("\n" + "-" * 30)
        print("           ROTTA")
        print("-" * 30)
        print("1 - Cadastrar usuário")
        print("2 - Validar atividade")
        print("3 - Visualizar pontos")
        print("4 - Converter pontos")
        print("5 - Chatbot")
        print("6 - Excluir usuário")
        print("7 - Gerar QR Code")
        print("0 - Sair")
        print("-" * 30)

        opcao = input("Escolha uma opção: ").strip()
        print("-" * 30)

        match opcao:

            case "1":
                validar_atividade()

            case "2":
                visualizar_pontos()

            case "3":
                converter_pontos()

            case "4":
                chatbot()

            case "5":
                desativar_conta()

            case "6":
                gerar_qrcode()

            case "0":
                print("\nEncerrando sistema...")
                break

            case _:
                print("Opção inválida.")
def login():
    print("\n----- LOGIN -----")

    email = input("Digite seu e-mail: ").strip()
    senha = input("Digite sua senha: ").strip()

    for usuario in usuarios:
        if usuario["email"] == email and usuario["senha"] == senha:
            print(f"\nBem-vindo, {usuario['nome']}!")
            time.sleep(1)
            return True

    print("\nE-mail ou senha incorretos.")
    time.sleep(1.5)
    return False
while True:

    print("\n" + "-" * 30)
    print("        LOGIN ROTTA")
    print("-" * 30)
    print("1 - Login")
    print("2 - Cadastrar usuário")
    print("0 - Sair")
    print("-" * 30)

    escolha = input("Escolha uma opção: ").strip()

    match escolha:

        case "1":

            acesso = login()

            if acesso:
                menu()

        case "2":
            cadastrar_usuario()

        case "0":
            print("\nEncerrando sistema.")
            break

        case _:
            print("Opção inválida.")