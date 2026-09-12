#THIAGO RODRIGUES SANTA ROSA – RM572616
#GUILHERME MATHEUS MAGALHÃES ALMEIDA – RM571713
#LEONARDO ARNALDO CERQUEIRA DA SILVA – RM573188
#BEATRIZ URBANO MARQUES DE OLIVEIRA – RM569341
#GEOVANNA SECCHI EGEA – RM573452

import json
import os
import time
from datetime import datetime

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_PONTOS = "pontos.json"
ARQUIVO_HISTORICO = "historico.json"
ARQUIVO_CONSULTAS_CRUD = "consultas_crud.json"

# PERSISTÊNCIA (usuários)

def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        return []

    try:
        with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (json.JSONDecodeError, OSError) as erro:
        print(f"Aviso: não foi possível ler {ARQUIVO_USUARIOS} ({erro}). Iniciando lista vazia.")
        return []


def salvar_usuarios(usuarios):
    try:
        with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as arquivo:
            json.dump(usuarios, arquivo, ensure_ascii=False, indent=4)
    except OSError as erro:
        print(f"Erro ao salvar usuários: {erro}")
        return False
    else:
        return True
    finally:
        pass

# PONTUACAO

def carregar_pontos():
    if not os.path.exists(ARQUIVO_PONTOS):
        return 0

    try:
        with open(ARQUIVO_PONTOS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
            return dados.get("saldo_pontos", 0)
    except (json.JSONDecodeError, OSError) as erro:
        print(f"Aviso: não foi possível ler {ARQUIVO_PONTOS} ({erro}). Saldo iniciado em 0.")
        return 0


def salvar_pontos(saldo_pontos): #salva dados no json
    try:
        with open(ARQUIVO_PONTOS, "w", encoding="utf-8") as arquivo:
            json.dump({"saldo_pontos": saldo_pontos}, arquivo, ensure_ascii=False, indent=4)
    except OSError as erro:
        print(f"Erro ao salvar pontos: {erro}")
        return False
    else:
        return True

# PERSISTENCIA (histórico de eventos) — sequencia de TUPLAS


def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return []

    try:
        with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
            return [tuple(evento) for evento in dados]
    except (json.JSONDecodeError, OSError) as erro:
        print(f"Aviso: não foi possível ler {ARQUIVO_HISTORICO} ({erro}). Histórico iniciado vazio.")
        return []


def salvar_historico(historico):
    try:
        with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as arquivo:
            json.dump([list(evento) for evento in historico], arquivo, ensure_ascii=False, indent=4)
    except OSError as erro:
        print(f"Erro ao salvar histórico: {erro}")
        return False
    else:
        return True


def registrar_evento(historico, tipo, pontos):
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    evento = (data_hora, tipo, pontos)

    try:
        historico.append(evento)
        salvar_historico(historico)
    except Exception as erro:
        print(f"Erro ao registrar evento no histórico: {erro}")

    return historico


def filtrar_historico_por_tipo(historico, tipo):
    return [evento for evento in historico if evento[1].lower() == tipo.lower()]


def listar_historico(historico):

    if not historico:
        print("Nenhum evento encontrado.")
        return

    for data_hora, tipo, pontos in historico:
        sinal = "+" if pontos >= 0 else ""
        print(f"[{data_hora}] {tipo.upper():10s} {sinal}{pontos} pontos")

# VALIDACÃO DE DADOS

def email_valido(email):
    if "@" not in email or "." not in email:
        return False

    usuario, _, dominio = email.partition("@")
    return usuario != "" and "." in dominio and not dominio.startswith(".")


def buscar_usuario_por_email(usuarios, email):
    for usuario in usuarios:
        if usuario["email"] == email:
            return usuario
    return None


def filtrar_usuarios_por_nome(usuarios, termo_busca):
    termo_busca = termo_busca.strip().lower()
    return [usuario for usuario in usuarios if termo_busca in usuario["nome"].lower()]


def ordenar_usuarios_por_nome(usuarios):
    return sorted(usuarios, key=lambda usuario: usuario["nome"].lower())

# REGISTRO E EXPORTACÃO DAS CONSULTAS CRUD

def registrar_consulta_crud(registro_crud, operacao, dados):
    consulta = {
        "operacao": operacao,
        "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "dados": dados,
    }
    registro_crud.append(consulta)
    return registro_crud


def exportar_consultas_crud(registro_crud):
    print("\n----- EXPORTAR CONSULTAS CRUD -----")

    try:
        if not registro_crud:
            raise ValueError("Nenhuma operação de CRUD foi realizada nesta sessão ainda.")

        with open(ARQUIVO_CONSULTAS_CRUD, "w", encoding="utf-8") as arquivo:
            json.dump(registro_crud, arquivo, ensure_ascii=False, indent=4)

    except ValueError as erro:
        print(f"Erro: {erro}")
        return False
    except OSError as erro:
        print(f"Erro ao exportar consultas: {erro}")
        return False
    else:
        print(f"{len(registro_crud)} operação(ões) exportada(s) para '{ARQUIVO_CONSULTAS_CRUD}' com sucesso!")
        return True
    finally:
        print("Exportação de consultas CRUD finalizada.")


# CRUD DE USUARIOS

def cadastrar_usuario(usuarios, registro_crud):
    print("\n----- CADASTRO DE USUÁRIO -----")

    nome = input("Digite seu nome: ").strip()
    while nome == "":
        nome = input("Nome inválido. Digite novamente: ").strip()

    email = input("Digite seu e-mail: ").strip()
    while not email_valido(email):
        email = input("E-mail inválido. Digite novamente: ").strip()

    if buscar_usuario_por_email(usuarios, email):
        print("Já existe um usuário com este e-mail.")
        return usuarios, registro_crud

    senha = input("Digite sua senha: ").strip()
    while len(senha) < 4:
        senha = input("Senha inválida (mínimo 4 caracteres). Digite novamente: ").strip()

    novo_usuario = {"nome": nome, "email": email, "senha": senha}

    try:
        usuarios.append(novo_usuario)
        sucesso = salvar_usuarios(usuarios)
    except Exception as erro:
        print(f"Erro inesperado ao cadastrar usuário: {erro}")
    else:
        if sucesso:
            print(f"\nUsuário {nome} cadastrado com sucesso!")
            registro_crud = registrar_consulta_crud(
                registro_crud, "create", {"nome": nome, "email": email}
            )
    finally:
        print("Operação de cadastro finalizada.")

    return usuarios, registro_crud


def editar_usuario(usuarios, registro_crud):
    print("\n----- EDITAR USUÁRIO -----")

    email = input("Digite o e-mail do usuário que deseja editar: ").strip()

    try:
        usuario = buscar_usuario_por_email(usuarios, email)

        if usuario is None:
            raise ValueError("E-mail não encontrado.")

        novo_nome = input(f"Novo nome (Enter para manter '{usuario['nome']}'): ").strip()
        nova_senha = input("Nova senha (Enter para manter a atual, mínimo 4 caracteres): ").strip()

        if novo_nome != "":
            usuario["nome"] = novo_nome

        if nova_senha != "":
            while len(nova_senha) < 4:
                nova_senha = input("Senha inválida (mínimo 4 caracteres). Digite novamente: ").strip()
            usuario["senha"] = nova_senha

    except ValueError as erro:
        print(f"Erro: {erro}")
    else:
        salvar_usuarios(usuarios)
        print("Usuário atualizado com sucesso!")
        registro_crud = registrar_consulta_crud(
            registro_crud, "update", {"nome": usuario["nome"], "email": usuario["email"]}
        )
    finally:
        print("Operação de edição finalizada.")

    return usuarios, registro_crud


def excluir_usuario(usuarios, registro_crud):
    print("\n----- EXCLUIR USUÁRIO -----")

    email = input("Digite o e-mail do usuário: ").strip()

    try:
        usuario = buscar_usuario_por_email(usuarios, email)

        if usuario is None:
            raise ValueError("E-mail não encontrado.")

        usuarios.remove(usuario)

    except ValueError as erro:
        print(f"Erro: {erro}")
    else:
        salvar_usuarios(usuarios)
        print("Conta excluída com sucesso.")
        registro_crud = registrar_consulta_crud(
            registro_crud, "delete", {"nome": usuario["nome"], "email": usuario["email"]}
        )
    finally:
        print("Operação de exclusão finalizada.")

    return usuarios, registro_crud


def listar_usuarios(usuarios):
    print("\n----- USUÁRIOS CADASTRADOS -----")

    if not usuarios:
        print("Nenhum usuário cadastrado.")
        return

    for indice, usuario in enumerate(usuarios, start=1):
        print(f"{indice}. {usuario['nome']} - {usuario['email']}")


def consultar_usuario(usuarios, registro_crud):
    print("\n----- CONSULTAR USUÁRIO -----")

    email = input("Digite o e-mail do usuário a consultar: ").strip()

    try:
        usuario = buscar_usuario_por_email(usuarios, email)

        if usuario is None:
            raise ValueError("E-mail não encontrado.")

    except ValueError as erro:
        print(f"Erro: {erro}")
    else:
        print(f"Nome: {usuario['nome']}")
        print(f"E-mail: {usuario['email']}")
        registro_crud = registrar_consulta_crud(
            registro_crud, "read", {"nome": usuario["nome"], "email": usuario["email"]}
        )
    finally:
        print("Consulta finalizada.")

    return registro_crud


def buscar_usuarios_menu(usuarios, registro_crud):
    print("\n----- BUSCAR / ORGANIZAR USUÁRIOS -----")
    print("1 - Consultar usuário por e-mail")
    print("2 - Filtrar por nome")
    print("3 - Listar todos em ordem alfabética")
    opcao = input("Escolha uma opção: ").strip()

    try:
        if opcao == "1":
            registro_crud = consultar_usuario(usuarios, registro_crud)
        elif opcao == "2":
            termo = input("Digite parte do nome a buscar: ").strip()
            if termo == "":
                raise ValueError("Termo de busca não pode ser vazio.")
            resultado = filtrar_usuarios_por_nome(usuarios, termo)
            listar_usuarios(resultado)
        elif opcao == "3":
            listar_usuarios(ordenar_usuarios_por_nome(usuarios))
        else:
            print("Opção inválida.")
    except ValueError as erro:
        print(f"Erro: {erro}")
    finally:
        print("Busca finalizada.")

    return registro_crud


def login(usuarios):
    print("\n----- LOGIN -----")

    email = input("Digite seu e-mail: ").strip()
    senha = input("Digite sua senha: ").strip()

    usuario = buscar_usuario_por_email(usuarios, email)

    if usuario is not None and usuario["senha"] == senha:
        print(f"\nBem-vindo, {usuario['nome']}!")
        time.sleep(1)
        return usuario

    print("\nE-mail ou senha incorretos.")
    time.sleep(1.5)
    return None

# PONTOS E RECOMPENSAS

def validar_atividade(saldo_pontos, historico):
    print("\n----- VALIDAR ATIVIDADE -----")

    comprovante = input("Informe o comprovante: ").strip()

    try:
        if comprovante == "":
            raise ValueError("Comprovante inválido.")

        print("IA analisando comprovante...\n")
        time.sleep(2)
        print("Comprovante aprovado!\n")

        saldo_pontos += 50

    except ValueError as erro:
        print(f"Erro: {erro}")
    else:
        salvar_pontos(saldo_pontos)
        historico = registrar_evento(historico, "atividade", 50)
        time.sleep(1.5)
        print("Você ganhou 50 pontos!\n")
        print(f"Saldo atual: {saldo_pontos} pontos.")
    finally:
        print("Validação de atividade finalizada.")

    return saldo_pontos, historico


def visualizar_pontos(saldo_pontos):
    print("\n----- SALDO DE PONTOS -----")
    print(f"Você possui {saldo_pontos} pontos.")


def converter_pontos(saldo_pontos, historico):
    print("\n----- CONVERTER PONTOS -----")

    try:
        if saldo_pontos < 100:
            raise ValueError("Pontos insuficientes.")

        saldo_pontos -= 100

    except ValueError as erro:
        print(f"Erro: {erro}")
    else:
        salvar_pontos(saldo_pontos)
        historico = registrar_evento(historico, "conversao", -100)
        print("Passagem gerada com sucesso!")
        print(f"Saldo restante: {saldo_pontos} pontos.")
    finally:
        print("Conversão de pontos finalizada.")

    return saldo_pontos, historico


def gerar_qrcode(saldo_pontos, historico):
    print("\n----- GERAR QR CODE -----")

    try:
        if saldo_pontos < 150:
            raise ValueError("Você precisa de 150 pontos para gerar o QR Code.")

        saldo_pontos -= 150

    except ValueError as erro:
        print(f"Erro: {erro}")
        print(f"Saldo atual: {saldo_pontos} pontos.")
    else:
        salvar_pontos(saldo_pontos)
        historico = registrar_evento(historico, "qrcode", -150)

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
    finally:
        print("Geração de QR Code finalizada.")

    return saldo_pontos, historico


def menu_historico(historico):
    print("\n----- HISTÓRICO DE PONTOS -----")
    print("1 - Ver histórico completo")
    print("2 - Filtrar por tipo (atividade, conversao, qrcode)")
    opcao = input("Escolha uma opção: ").strip()

    try:
        if opcao == "1":
            listar_historico(historico)
        elif opcao == "2":
            tipo = input("Digite o tipo a filtrar: ").strip()
            if tipo == "":
                raise ValueError("Tipo não pode ser vazio.")
            listar_historico(filtrar_historico_por_tipo(historico, tipo))
        else:
            print("Opção inválida.")
    except ValueError as erro:
        print(f"Erro: {erro}")
    finally:
        print("Consulta ao histórico finalizada.")


# CHATBOT

def chatbot():
    print("\n----- CAPI CHATBOT -----")

    pergunta = input("Digite sua dúvida: ").strip()

    if pergunta:
        print("Sua solicitação foi registrada.")
    else:
        print("Nenhuma pergunta informada.")

def enviar_creditos(saldo_pontos, historico):
    print("\n----- ENVIAR CREDITOS PARA CARTAO ROTTA -----")

    enviar = input("Deseja converter seus pontos em credito? S/N: ").strip().upper()

    if enviar == "S":
        print("Creditos enviados para o Cartao ROTTA!")

    elif enviar == "N":
        print("Conversao cancelada.")

    else:
        print("Opcao invalida.") 

    return saldo_pontos, historico


# MENUS (com submenus)

def menu_pontos_recompensas(saldo_pontos, historico):
    while True:
        print("\n" + "-" * 30)
        print("     PONTOS E RECOMPENSAS")
        print("-" * 30)
        print("1 - Validar atividade")
        print("2 - Visualizar pontos")
        print("3 - Converter pontos em passagem")
        print("4 - Gerar QR Code")
        print("5 - Enviar creditos para cartão ROTTA")
        print("6 - Ver histórico de pontos")
        print("0 - Voltar")
        print("-" * 30)

        opcao = input("Escolha uma opção: ").strip()
        print("-" * 30)

        match opcao:
            case "1":
                saldo_pontos, historico = validar_atividade(saldo_pontos, historico)
            case "2":
                visualizar_pontos(saldo_pontos)
            case "3":
                saldo_pontos, historico = converter_pontos(saldo_pontos, historico)
            case "4":
                saldo_pontos, historico = gerar_qrcode(saldo_pontos, historico)
            case "5":
                saldo_pontos, historico = enviar_creditos(saldo_pontos, historico)
            case "6":
                menu_historico(historico)
            case "0":
                break
            case _:
                print("Opção inválida.")

    return saldo_pontos, historico


def menu_minha_conta(usuarios, registro_crud):
    while True:
        print("\n" + "-" * 30)
        print("         MINHA CONTA")
        print("-" * 30)
        print("1 - Editar meu cadastro")
        print("2 - Excluir minha conta")
        print("0 - Voltar")
        print("-" * 30)

        opcao = input("Escolha uma opção: ").strip()
        print("-" * 30)

        match opcao:
            case "1":
                usuarios, registro_crud = editar_usuario(usuarios, registro_crud)
            case "2":
                usuarios, registro_crud = excluir_usuario(usuarios, registro_crud)
            case "0":
                break
            case _:
                print("Opção inválida.")

    return usuarios, registro_crud


def menu_usuario(usuarios, saldo_pontos, historico, registro_crud):
    while True:
        print("\n" + "-" * 30)
        print("           ROTTA")
        print("-" * 30)
        print("1 - Pontos e recompensas")
        print("2 - Minha conta")
        print("3 - Buscar / consultar usuários")
        print("4 - Chatbot")
        print("9 - Exportar consultas CRUD para JSON")
        print("0 - Sair")
        print("-" * 30)

        opcao = input("Escolha uma opção: ").strip()
        print("-" * 30)

        match opcao:
            case "1":
                saldo_pontos, historico = menu_pontos_recompensas(saldo_pontos, historico)
            case "2":
                usuarios, registro_crud = menu_minha_conta(usuarios, registro_crud)
            case "3":
                registro_crud = buscar_usuarios_menu(usuarios, registro_crud)
            case "4":
                chatbot()
            case "9":
                exportar_consultas_crud(registro_crud)
            case "0":
                print("\nEncerrando sistema...")
                break
            case _:
                print("Opção inválida.")

    return usuarios, saldo_pontos, historico, registro_crud


def menu_inicial():
    usuarios = carregar_usuarios()
    saldo_pontos = carregar_pontos()
    historico = carregar_historico()
    registro_crud = []

    while True:
        print("\n" + "-" * 30)
        print("        LOGIN ROTTA")
        print("-" * 30)
        print("1 - Login")
        print("2 - Cadastrar usuário")
        print("3 - Listar usuários")
        print("0 - Sair")
        print("-" * 30)

        escolha = input("Escolha uma opção: ").strip()

        match escolha:
            case "1":
                usuario_logado = login(usuarios)
                if usuario_logado is not None:
                    usuarios, saldo_pontos, historico, registro_crud = menu_usuario(
                        usuarios, saldo_pontos, historico, registro_crud
                    )
            case "2":
                usuarios, registro_crud = cadastrar_usuario(usuarios, registro_crud)
            case "3":
                listar_usuarios(usuarios)
            case "0":
                print("\nEncerrando sistema.")
                break
            case _:
                print("Opção inválida.")

if __name__ == "__main__":
    menu_inicial()