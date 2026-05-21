import json
import os

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


def listar_usuarios():
    print("\n----- LISTA DE USUÁRIOS -----")

    if not usuarios:
        print("Nenhum usuário cadastrado.")
        return

    for i, usuario in enumerate(usuarios, start=1):
        print(f"{i}. {usuario['nome']} - {usuario['email']}")


def validar_atividade():
    global saldo_pontos

    print("\n----- VALIDAR ATIVIDADE -----")

    comprovante = input("Informe o comprovante: ").strip()

    if comprovante == "":
        print("Comprovante inválido.")
        return

    print("IA analisando comprovante...")
    print("Comprovante aprovado!")

    saldo_pontos += 50

    salvar_pontos()

    print("Você ganhou 50 pontos!")
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


def ranking():
    print("\n----- RANKING -----")
    print("1º Rotta - 1250 pontos")
    print("2º Rank up - 980 pontos")
    print(f"3º Você - {saldo_pontos} pontos")


def chatbot():
    print("\n----- Rottinha CHATBOT -----")

    pergunta = input("Digite sua dúvida: ").strip()

    if pergunta:
        print("Sua solicitação foi registrada.")
    else:
        print("Nenhuma pergunta informada.")


def excluir_usuario():
    print("\n----- EXCLUIR USUÁRIO -----")

    email = input("Digite o e-mail do usuário: ").strip()

    for usuario in usuarios:
        if usuario["email"] == email:
            usuarios.remove(usuario)
            salvar_usuarios()
            print("Usuário removido com sucesso.")
            return

    print("Usuário não encontrado.")


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
██ ▄▄▄▄▄ ██▀▄█ ▄▄▄▄▄ ██
██ █   █ █ ▀ █ █   █ ██
██ █▄▄▄█ █▄▀▄█ █▄▄▄█ ██
██▄▄▄▄▄▄▄█▄█▄█▄▄▄▄▄▄▄██
██ ▄▀▄ ▄▀█ ▄█ ▄ ▄▀█▄ ██
██▄█▀▄▄▄█▄▀▀▀▄█▄▄▀██▄██
██ ▄▄▄▄▄ █▄ ▄ ▄█▀▄▀▄██
██ █   █ █▀█▄▄▀▀▄▀█▄██
██ █▄▄▄█ █ ▄▀█▄▀▀█▄██
██▄▄▄▄▄▄▄█▄▄▄██▄█▄▄▄██
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
        print("2 - Listar usuários")
        print("3 - Validar atividade")
        print("4 - Visualizar pontos")
        print("5 - Converter pontos")
        print("6 - Ranking")
        print("7 - Chatbot")
        print("8 - Excluir usuário")
        print("9 - Gerar QR Code")
        print("0 - Sair")
        print("-" * 30)

        opcao = input("Escolha uma opção: ").strip()
        print("-" * 30)

        match opcao:
            case "1":
                cadastrar_usuario()

            case "2":
                listar_usuarios()

            case "3":
                validar_atividade()

            case "4":
                visualizar_pontos()

            case "5":
                converter_pontos()

            case "6":
                ranking()

            case "7":
                chatbot()

            case "8":
                excluir_usuario()

            case "9":
                gerar_qrcode()

            case "0":
                print("\nEncerrando sistema.")
                break

            case _:
                print("Opção inválida.")


menu()