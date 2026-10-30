# THIAGO RODRIGUES SANTA ROSA - RM572616
# GUILHERME MATHEUS MAGALHAES ALMEIDA - RM571713
# LEONARDO ARNALDO CERQUEIRA DA SILVA - RM573188
# BEATRIZ URBANO MARQUES DE OLIVEIRA - RM569341
# GEOVANNA SECCHI EGEA - RM573452
"""ROTTA Sprint 4: demonstrador com persistência Oracle.

Executar primeiro ROTTA_BANCO_PYTHON_COMPLETO.sql no SQL Developer.
A conexão Oracle e o login da ROTTA são etapas diferentes.
IA e transporte são simulados; os dados são gravados de verdade no Oracle.
"""
import json
import os
from datetime import datetime, date
from decimal import Decimal
from getpass import getpass
from pathlib import Path
import banco_rotta as banco
import api_clima

PASTA = Path(__file__).resolve().parent


def registrar_consulta_crud(registros, operacao, dados):
    """Guarda operações da sessão para exportação; não recebe senhas."""
    registros.append({'operacao': operacao, 'data_hora': datetime.now().isoformat(timespec='seconds'), 'dados': dados})


def mostrar(linhas):
    """Exibe dicionários retornados pelas consultas do banco."""
    if not linhas:
        print('Nenhum registro encontrado.')
    for linha in linhas:
        print(' | '.join(f'{nome}: {valor}' for nome, valor in linha.items()))


def serializar_json(valor):
    """Converte datas e números retornados pelo Oracle para JSON."""
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return int(valor) if valor == valor.to_integral_value() else str(valor)
    raise TypeError(f'Tipo não suportado: {type(valor).__name__}')


def exportar_consultas_crud(conexao, usuario, registros):
    """Exporta dados consultados no Oracle e as operações da sessão atual."""
    uid = usuario['id_usuario']
    dados = {
        'usuario': banco.minha_conta(conexao, uid),
        'saldo_pontos': banco.saldo(conexao, uid),
        'atividades': banco.minhas_atividades(conexao, uid),
        'movimentacoes': banco.historico(conexao, uid),
        'resgates': banco.meus_resgates(conexao, uid),
        'operacoes_da_sessao': registros,
    }
    pasta = PASTA / 'exportacoes'
    pasta.mkdir(exist_ok=True)
    arquivo = pasta / f'consultas_usuario_{uid}_{datetime.now():%Y%m%d_%H%M%S_%f}.json'
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=4, default=serializar_json), encoding='utf-8')
    print(f'Consultas exportadas para: {arquivo}')


def cadastrar_usuario(conexao):
    """Coleta os dados e cadastra uma nova conta ROTTA com carteira vazia."""
    nome = input('Nome: ')
    email = input('E-mail: ')
    senha = input('Senha da ROTTA (4 a 128 caracteres): ')
    if senha != input('Repita a senha: '):
        raise ValueError('As senhas não conferem.')
    uid = banco.cadastrar(conexao, nome, email, senha)
    print(f'Usuário cadastrado! ID: {uid}. Sua carteira começa com zero pontos.')
    return uid


def login(conexao):
    """Autentica a conta da ROTTA, não as credenciais do Oracle."""
    email = input('E-mail da ROTTA: ')
    senha = input('Senha da ROTTA: ')
    usuario = banco.autenticar(conexao, email, senha)
    if usuario:
        print(f"Bem-vindo, {usuario['nm_usuario']}!")
    else:
        print('E-mail ou senha incorretos.')
    return usuario


def editar_usuario(conexao, usuario, registros):
    """Edita nome/senha da conta autenticada, sem escolher outra conta."""
    atual = banco.minha_conta(conexao, usuario['id_usuario'])
    nome = input(f"Novo nome (Enter mantém {atual['nm_usuario']}): ").strip() or atual['nm_usuario']
    senha = input('Nova senha (Enter mantém a atual): ')
    banco.editar(conexao, usuario['id_usuario'], nome, senha)
    usuario['nm_usuario'] = nome
    registrar_consulta_crud(registros, 'update', dict(usuario))
    print('Cadastro atualizado e salvo no Oracle.')


def excluir_usuario(conexao, usuario, registros):
    """Após confirmação, apaga a conta e seus dados; retorna True para sair."""
    print('A exclusão remove sua conta, saldo, atividades, histórico e resgates.')
    if input('Confirmar exclusão da SUA conta? S/N: ').strip().upper() != 'S':
        print('Exclusão cancelada.')
        return False
    # Salva a evidência do CRUD em memória apenas após a exclusão bem-sucedida.
    banco.excluir(conexao, usuario['id_usuario'])
    registrar_consulta_crud(registros, 'delete', dict(usuario))
    print('Conta excluída. Sessão encerrada.')
    return True


def validar_atividade(conexao, usuario):
    """Seleciona desafio, guarda comprovação textual e simula sua análise."""
    mostrar(banco.desafios(conexao))
    did = int(input('ID do desafio: '))
    descricao = input('Descreva a ação realizada (obrigatório): ')
    referencia = input('Caminho ou URL da foto/vídeo (opcional, apenas referência): ')
    print('DEMONSTRAÇÃO: não há análise real de imagem ou IA nesta versão.')
    resultado = input('Simular resultado: 1 - aprovado / 2 - rejeitado / 0 - cancelar: ').strip()
    if resultado == '0':
        return
    if resultado not in ('1', '2'):
        raise ValueError('Escolha 1, 2 ou 0.')
    pontos = banco.registrar_atividade(conexao, usuario['id_usuario'], did, descricao, referencia, resultado == '1')
    print(f'Resultado simulado salvo. Pontos creditados: {pontos}.')


def converter_pontos(conexao, usuario, tipo):
    """Confirma e registra o resgate simulado na carteira individual."""
    custo = banco.CUSTOS_RESGATE[tipo]
    if input(f'Resgate DEMONSTRATIVO {tipo}: {custo} pontos. Confirmar? S/N: ').strip().upper() != 'S':
        print('Resgate cancelado.')
        return
    if tipo == 'QRCODE':
        try:
            import qrcode
        except ModuleNotFoundError:
            print('Instale antes: python -m pip install qrcode')
            return
    codigo, custo = banco.resgatar(conexao, usuario['id_usuario'], tipo)
    print(f'Resgate simulado salvo: {codigo}. Débito: {custo} pontos.')
    print('Não é uma passagem válida e não envia créditos a um cartão real.')
    if tipo == 'QRCODE':
        qr = qrcode.QRCode(border=1)
        qr.add_data(codigo)
        qr.make(fit=True)
        qr.print_ascii()


def menu_historico(conexao, usuario):
    """Lista o histórico completo ou filtra por créditos/resgates."""
    opcao = input('1 - Completo / 2 - Créditos / 3 - Resgates: ').strip()
    if opcao not in ('1', '2', '3'):
        raise ValueError('Opção inválida.')
    mostrar(banco.historico(conexao, usuario['id_usuario'], {'1': None, '2': 'CREDITO', '3': 'RESGATE'}[opcao]))


def executar_acao(conexao, funcao, *args):
    """Trata falhas de entrada, arquivos e Oracle sem encerrar o menu."""
    import oracledb
    try:
        return funcao(*args)
    except (ValueError, OSError) as erro:
        print(f'Não foi possível concluir: {erro}')
    except oracledb.Error as erro:
        conexao.rollback()
        detalhe = erro.args[0]
        if getattr(detalhe, 'code', None) == 1:
            print('Já existe um registro com esse identificador, como o e-mail informado.')
        else:
            print(f'Erro do Oracle: {erro}')
    return None


def menu_pontos_recompensas(conexao, usuario):
    """Mantém o submenu de pontos, agora com persistência Oracle."""
    while True:
        print('\nPONTOS E RECOMPENSAS\n1 - Registrar atividade (simulação)\n2 - Ver saldo\n3 - Converter em passagem (simulação)\n4 - Gerar QR Code demonstrativo\n5 - Créditos para cartão (simulação)\n6 - Histórico\n7 - Minhas atividades\n8 - Meus resgates\n0 - Voltar')
        opcao = input('Opção: ').strip()
        match opcao:
            case '1': executar_acao(conexao, validar_atividade, conexao, usuario)
            case '2': executar_acao(conexao, lambda: print(f"Saldo: {banco.saldo(conexao, usuario['id_usuario'])} pontos."))
            case '3' | '4' | '5': executar_acao(conexao, converter_pontos, conexao, usuario, {'3':'PASSAGEM','4':'QRCODE','5':'CARTAO'}[opcao])
            case '6': executar_acao(conexao, menu_historico, conexao, usuario)
            case '7': executar_acao(conexao, lambda: mostrar(banco.minhas_atividades(conexao, usuario['id_usuario'])))
            case '8': executar_acao(conexao, lambda: mostrar(banco.meus_resgates(conexao, usuario['id_usuario'])))
            case '0': return
            case _: print('Opção inválida.')


def menu_minha_conta(conexao, usuario, registros):
    """Retorna True após excluir a conta, encerrando também o menu principal."""
    while True:
        print('\nMINHA CONTA\n1 - Editar meu cadastro\n2 - Excluir minha conta\n0 - Voltar')
        match input('Opção: ').strip():
            case '1': executar_acao(conexao, editar_usuario, conexao, usuario, registros)
            case '2':
                if executar_acao(conexao, excluir_usuario, conexao, usuario, registros):
                    return True
            case '0': return False
            case _: print('Opção inválida.')


def consultar_usuario(conexao, usuario, registros):
    """Consulta e registra os dados da própria conta para demonstrar o READ."""
    dados = banco.minha_conta(conexao, usuario['id_usuario'])
    mostrar([dados])
    registrar_consulta_crud(registros, 'read', dados)


def chatbot():
    """Mantém a área Capi, identificada como recurso ainda não integrado."""
    print('Capi: assistente ainda não integrado. Esta tela não registra atendimentos.')
    input('Pressione Enter para voltar.')


def menu_usuario(conexao, usuario, registros):
    """Encaminha sempre o ID autenticado às operações do banco."""
    while True:
        print('\nROTTA\n1 - Pontos e recompensas\n2 - Minha conta\n3 - Consultar meu cadastro\n4 - Capi\n5 - Clima para o deslocamento (API)\n9 - Exportar minhas consultas para JSON\n0 - Sair da conta')
        match input('Opção: ').strip():
            case '1': menu_pontos_recompensas(conexao, usuario)
            case '2':
                if menu_minha_conta(conexao, usuario, registros):
                    return
            case '3': executar_acao(conexao, consultar_usuario, conexao, usuario, registros)
            case '4': chatbot()
            case '5': executar_acao(conexao, api_clima.menu_clima, registros)
            case '9': executar_acao(conexao, exportar_consultas_crud, conexao, usuario, registros)
            case '0': return
            case _: print('Opção inválida.')


def menu_inicial(conexao):
    """Menu inicial de cadastro e login da ROTTA."""
    # Cada conta tem um registro de operações próprio, apenas nesta execução.
    registros = {}
    while True:
        print('\nLOGIN ROTTA\n1 - Login\n2 - Cadastrar usuário\n0 - Encerrar')
        match input('Opção: ').strip():
            case '1':
                usuario = executar_acao(conexao, login, conexao)
                if usuario:
                    menu_usuario(conexao, usuario, registros.setdefault(usuario['id_usuario'], []))
            case '2':
                uid = executar_acao(conexao, cadastrar_usuario, conexao)
                if uid:
                    registros[uid] = []
                    registrar_consulta_crud(registros[uid], 'create', {'id_usuario': uid})
            case '0': return
            case _: print('Opção inválida.')


def main():
    """Abre conexão no Oracle com SID; credenciais não são salvas."""
    try:
        import oracledb
    except ModuleNotFoundError:
        print('Instale as dependências: python -m pip install -r requirements.txt')
        return
    try:
        print('CONEXÃO ORACLE - utilize seu usuário da FIAP/SQL Developer.')
        usuario = os.environ.get('ROTTA_ORACLE_USER') or input('Usuário Oracle: ').strip()
        senha = os.environ.get('ROTTA_ORACLE_PASSWORD') or getpass('Senha Oracle: ')
        if not usuario or not senha:
            raise ValueError('Usuário e senha do Oracle são obrigatórios.')
        parametros = oracledb.ConnectParams(host='oracle.fiap.com.br', port=1521, sid='ORCL', tcp_connect_timeout=10, retry_count=0)
        with oracledb.connect(user=usuario, password=senha, params=parametros) as conexao:
            conexao.call_timeout = 20000
            print('Conectado. Agora use ou cadastre uma conta da ROTTA.')
            menu_inicial(conexao)
    except (KeyboardInterrupt, EOFError):
        print('\nPrograma encerrado. Operações pendentes não foram confirmadas.')
    except (oracledb.Error, ValueError) as erro:
        print(f'Não foi possível continuar: {erro}')


if __name__ == '__main__':
    main()
