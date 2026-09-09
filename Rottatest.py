"""
ROTTA - Sistema de mobilidade urbana sustentável (SoulUp)
Sprint 3 - Computational Thinking Using Python

Módulo responsável por:
- Cadastro, login, edição e exclusão de usuários (CRUD)
- Validação de atividades/postagens (simulação de IA)
- Controle de saldo de pontos e conversão em créditos
- Geração de QR Code para resgate
- Chatbot de suporte (Rottinha)
"""

import json
import os
import time

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_PONTOS = "pontos.json"


def carregar_usuarios():
    """
    Carrega a lista de usuários a partir do arquivo JSON.

    Retorno:
        list[dict]: lista de usuários (nome, email, senha).
                    Retorna lista vazia se o arquivo não existir ou estiver corrompido.
    """
    if not os.path.exists(ARQUIVO_USUARIOS):
        return []

    try:
        with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (json.JSONDecodeError, OSError) as erro:
        print(f"Aviso: não foi possível ler {ARQUIVO_USUARIOS} ({erro}). Iniciando lista vazia.")
        return []


def salvar_usuarios(usuarios):
    """
    Salva a lista de usuários no arquivo JSON.

    Parâmetros:
        usuarios (list[dict]): lista de usuários a ser persistida.

    Retorno:
        bool: True se salvou com sucesso, False caso contrário.
    """
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


def carregar_pontos():
    """
    Carrega o saldo de pontos a partir do arquivo JSON.

    Retorno:
        int: saldo de pontos. Retorna 0 se o arquivo não existir ou estiver corrompido.
    """
    if not os.path.exists(ARQUIVO_PONTOS):
        return 0

    try:
        with open(ARQUIVO_PONTOS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
            return dados.get("saldo_pontos", 0)
    except (json.JSONDecodeError, OSError) as erro:
        print(f"Aviso: não foi possível ler {ARQUIVO_PONTOS} ({erro}). Saldo iniciado em 0.")
        return 0


def salvar_pontos(saldo_pontos):
    """
    Salva o saldo de pontos no arquivo JSON.

    Parâmetros:
        saldo_pontos (int): saldo atual a ser persistido.

    Retorno:
        bool: True se salvou com sucesso, False caso contrário.
    """
    try:
        with open(ARQUIVO_PONTOS, "w", encoding="utf-8") as arquivo:
            json.dump({"saldo_pontos": saldo_pontos}, arquivo, ensure_ascii=False, indent=4)
    except OSError as erro:
        print(f"Erro ao salvar pontos: {erro}")
        return False
    else:
        return True


def email_valido(email):
    """
    Valida um formato simples de e-mail.

    Parâmetros:
        email (str): e-mail a ser validado.

    Retorno:
        bool: True se o e-mail contém '@' e '.', False caso contrário.
    """
    return "@" in email and "." in email


def buscar_usuario_por_email(usuarios, email):
    """
    Procura um usuário na lista pelo e-mail.

    Parâmetros:
        usuarios (list[dict]): lista de usuários.
        email (str): e-mail a ser buscado.

    Retorno:
        dict | None: o usuário encontrado, ou None se não existir.
    """
    for usuario in usuarios:
        if usuario["email"] == email:
            return usuario
    return None


def cadastrar_usuario(usuarios):
    """
    Cadastra um novo usuário (Create), com validação de nome, e-mail e senha.

    Parâmetros:
        usuarios (list[dict]): lista de usuários carregada em memória.

    Retorno:
        list[dict]: lista de usuários atualizada.
    """
    print("\n----- CADASTRO DE USUÁRIO -----")

    nome = input("Digite seu nome: ").strip()
    while nome == "":
        nome = input("Nome inválido. Digite novamente: ").strip()

    email = input("Digite seu e-mail: ").strip()
    while not email_valido(email):
        email = input("E-mail inválido. Digite novamente: ").strip()

    if buscar_usuario_por_email(usuarios, email):
        print("Já existe um usuário com este e-mail.")
        return usuarios

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
    finally:
        print("Operação de cadastro finalizada.")

    return usuarios


def editar_usuario(usuarios):
    """
    Edita os dados (nome e/ou senha) de um usuário existente (Update).

    Parâmetros:
        usuarios (list[dict]): lista de usuários carregada em memória.

    Retorno:
        list[dict]: lista de usuários atualizada.
    """
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
    finally:
        print("Operação de edição finalizada.")

    return usuarios


def excluir_usuario(usuarios):
    """
    Remove um usuário existente pelo e-mail (Delete).

    Parâmetros:
        usuarios (list[dict]): lista de usuários carregada em memória.

    Retorno:
        list[dict]: lista de usuários atualizada.
    """
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
    finally:
        print("Operação de exclusão finalizada.")

    return usuarios


def listar_usuarios(usuarios):
    """
    Lista (Read) todos os usuários cadastrados, exibindo nome e e-mail.

    Parâmetros:
        usuarios (list[dict]): lista de usuários carregada em memória.
    """
    print("\n----- USUÁRIOS CADASTRADOS -----")

    if not usuarios:
        print("Nenhum usuário cadastrado.")
        return

    for indice, usuario in enumerate(usuarios, start=1):
        print(f"{indice}. {usuario['nome']} - {usuario['email']}")


def login(usuarios):
    """
    Autentica um usuário pelo e-mail e senha.

    Parâmetros:
        usuarios (list[dict]): lista de usuários carregada em memória.

    Retorno:
        dict | None: o usuário autenticado, ou None se as credenciais forem inválidas.
    """
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


def validar_atividade(saldo_pontos):
    """
    Simula a validação de um comprovante de atividade via IA e credita pontos.

    Parâmetros:
        saldo_pontos (int): saldo de pontos atual.

    Retorno:
        int: saldo de pontos atualizado.
    """
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
        time.sleep(1.5)
        print("Você ganhou 50 pontos!\n")
        print(f"Saldo atual: {saldo_pontos} pontos.")
    finally:
        print("Validação de atividade finalizada.")

    return saldo_pontos


def visualizar_pontos(saldo_pontos):
    """
    Exibe o saldo de pontos atual.

    Parâmetros:
        saldo_pontos (int): saldo de pontos atual.
    """
    print("\n----- SALDO DE PONTOS -----")
    print(f"Você possui {saldo_pontos} pontos.")


def converter_pontos(saldo_pontos):
    """
    Converte 100 pontos em uma passagem, se houver saldo suficiente.

    Parâmetros:
        saldo_pontos (int): saldo de pontos atual.

    Retorno:
        int: saldo de pontos atualizado.
    """
    print("\n----- CONVERTER PONTOS -----")

    try:
        if saldo_pontos < 100:
            raise ValueError("Pontos insuficientes.")

        saldo_pontos -= 100

    except ValueError as erro:
        print(f"Erro: {erro}")
    else:
        salvar_pontos(saldo_pontos)
        print("Passagem gerada com sucesso!")
        print(f"Saldo restante: {saldo_pontos} pontos.")
    finally:
        print("Conversão de pontos finalizada.")

    return saldo_pontos


def chatbot():
    """
    Registra uma dúvida enviada pelo usuário ao chatbot Rottinha.
    """
    print("\n----- Rottinha CHATBOT -----")

    pergunta = input("Digite sua dúvida: ").strip()

    if pergunta:
        print("Sua solicitação foi registrada.")
    else:
        print("Nenhuma pergunta informada.")


def gerar_qrcode(saldo_pontos):
    """
    Gera um QR Code de resgate, descontando 150 pontos do saldo.

    Parâmetros:
        saldo_pontos (int): saldo de pontos atual.

    Retorno:
        int: saldo de pontos atualizado.
    """
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

    return saldo_pontos


def demonstrar_crud(usuarios):
    """
    Executa um exemplo de cada operação do CRUD (Create, Read, Update, Delete)
    sobre um usuário de demonstração e exporta o resultado de cada etapa
    para um arquivo JSON.

    Parâmetros:
        usuarios (list[dict]): lista de usuários carregada em memória.

    Retorno:
        list[dict]: lista de usuários atualizada (o usuário de demonstração
                    é removido ao final, preservando os dados reais).
    """
    print("\n----- DEMONSTRAÇÃO DO CRUD -----")

    resultado = {}
    email_demo = "demo.crud@rotta.com"

    try:
        # CREATE
        usuario_demo = {"nome": "Usuário Demonstração", "email": email_demo, "senha": "demo1234"}
        usuarios.append(usuario_demo)
        resultado["create"] = dict(usuario_demo)
        print(f"[CREATE] Usuário criado: {usuario_demo['nome']} ({usuario_demo['email']})")

        # READ
        usuario_lido = buscar_usuario_por_email(usuarios, email_demo)
        resultado["read"] = dict(usuario_lido)
        print(f"[READ] Usuário lido: {usuario_lido['nome']} ({usuario_lido['email']})")

        # UPDATE
        usuario_lido["nome"] = "Usuário Demonstração Editado"
        resultado["update"] = dict(usuario_lido)
        print(f"[UPDATE] Usuário atualizado: {usuario_lido['nome']}")

        # DELETE
        usuarios.remove(usuario_lido)
        resultado["delete"] = {"email_removido": email_demo, "status": "removido com sucesso"}
        print(f"[DELETE] Usuário removido: {email_demo}")

    except Exception as erro:
        print(f"Erro durante a demonstração do CRUD: {erro}")
    else:
        try:
            with open("resultado_crud.json", "w", encoding="utf-8") as arquivo:
                json.dump(resultado, arquivo, ensure_ascii=False, indent=4)
        except OSError as erro:
            print(f"Erro ao exportar resultado do CRUD: {erro}")
        else:
            print("\nResultado do CRUD exportado para 'resultado_crud.json' com sucesso!")
    finally:
        print("Demonstração do CRUD finalizada.")

    return usuarios


def menu_usuario(usuarios, saldo_pontos):
    """
    Exibe o menu principal do sistema (pós-login) e trata as opções escolhidas.

    Parâmetros:
        usuarios (list[dict]): lista de usuários carregada em memória.
        saldo_pontos (int): saldo de pontos atual.

    Retorno:
        tuple[list[dict], int]: usuários e saldo de pontos atualizados.
    """
    while True:
        print("\n" + "-" * 30)
        print("           ROTTA")
        print("-" * 30)
        print("1 - Validar atividade")
        print("2 - Visualizar pontos")
        print("3 - Converter pontos")
        print("4 - Chatbot")
        print("5 - Editar meu cadastro")
        print("6 - Excluir minha conta")
        print("7 - Gerar QR Code")
        print("8 - Demonstração do CRUD (exportar JSON)")
        print("0 - Sair")
        print("-" * 30)

        opcao = input("Escolha uma opção: ").strip()
        print("-" * 30)

        match opcao:
            case "1":
                saldo_pontos = validar_atividade(saldo_pontos)
            case "2":
                visualizar_pontos(saldo_pontos)
            case "3":
                saldo_pontos = converter_pontos(saldo_pontos)
            case "4":
                chatbot()
            case "5":
                usuarios = editar_usuario(usuarios)
            case "6":
                usuarios = excluir_usuario(usuarios)
            case "7":
                saldo_pontos = gerar_qrcode(saldo_pontos)
            case "8":
                usuarios = demonstrar_crud(usuarios)
            case "0":
                print("\nEncerrando sistema...")
                break
            case _:
                print("Opção inválida.")

    return usuarios, saldo_pontos


def menu_inicial():
    """
    Ponto de entrada do sistema: menu de login/cadastro e loop principal da aplicação.
    """
    usuarios = carregar_usuarios()
    saldo_pontos = carregar_pontos()

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
                    usuarios, saldo_pontos = menu_usuario(usuarios, saldo_pontos)
            case "2":
                usuarios = cadastrar_usuario(usuarios)
            case "3":
                listar_usuarios(usuarios)
            case "0":
                print("\nEncerrando sistema.")
                break
            case _:
                print("Opção inválida.")


if __name__ == "__main__":
    menu_inicial()
