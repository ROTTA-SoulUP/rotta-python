"""Persistência Oracle da ROTTA: consultas e transações do aplicativo."""
import hashlib
import hmac
import secrets
import re
from contextlib import contextmanager
from uuid import uuid4

# Regras demonstrativas; não representam tarifas reais nem integração com transporte.
CUSTOS_RESGATE = {"PASSAGEM": 100, "QRCODE": 150, "CARTAO": 100}


def gerar_hash(senha):
    """Retorna hash PBKDF2 com salt aleatório, sem armazenar a senha original."""
    if not 4 <= len(senha) <= 128:
        raise ValueError("A senha deve ter entre 4 e 128 caracteres.")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', senha.encode(), bytes.fromhex(salt), 600000)
    return f"pbkdf2_sha256$600000${salt}${digest.hex()}"


def verificar_senha(senha, valor):
    """Compara a senha fornecida com o hash armazenado."""
    try:
        algoritmo, repeticoes, salt, esperado = valor.split('$')
        if algoritmo != 'pbkdf2_sha256' or int(repeticoes) != 600000:
            return False
        obtido = hashlib.pbkdf2_hmac('sha256', senha.encode(), bytes.fromhex(salt), int(repeticoes))
        return hmac.compare_digest(obtido.hex(), esperado)
    except (ValueError, TypeError, AttributeError):
        return False


def validar_cadastro(nome, email):
    """Normaliza os campos e valida os limites da tabela."""
    nome, email = nome.strip(), email.strip().lower()
    if not 1 <= len(nome) <= 100:
        raise ValueError("Nome obrigatório, com até 100 caracteres.")
    if len(email) > 150 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise ValueError("E-mail inválido.")
    return nome, email


@contextmanager
def transacao(conexao):
    """Confirma todas as mudanças juntas ou desfaz a operação inteira."""
    try:
        with conexao.cursor() as cursor:
            yield cursor
        conexao.commit()
    except BaseException:
        conexao.rollback()
        raise


def consultar(conexao, sql, parametros=None):
    """Executa SELECT e retorna uma lista de dicionários, sem alterar dados."""
    with conexao.cursor() as cursor:
        cursor.execute(sql, parametros or {})
        nomes = [coluna[0].lower() for coluna in cursor.description]
        return [dict(zip(nomes, linha)) for linha in cursor.fetchall()]


def inserir_id(cursor, sql, parametros):
    """Executa INSERT com RETURNING e devolve o ID gerado pelo Oracle."""
    retorno = cursor.var(int)
    cursor.execute(sql, {**parametros, 'novo_id': retorno})
    return int(retorno.getvalue()[0])


def bloquear_usuario(cursor, id_usuario):
    """Confirma a existência da conta e serializa suas operações de escrita."""
    cursor.execute('SELECT ID_USUARIO FROM TB_USUARIO WHERE ID_USUARIO=:p_usuario_id FOR UPDATE', {'p_usuario_id': id_usuario})
    if cursor.fetchone() is None:
        raise ValueError("Conta não encontrada. Faça login novamente.")


def bloquear_carteira(cursor, id_usuario):
    """Retorna a carteira do usuário autenticado, bloqueada até commit/rollback."""
    bloquear_usuario(cursor, id_usuario)
    cursor.execute('SELECT ID_CARTEIRA, SALDO_PONTOS FROM TB_CARTEIRA WHERE ID_USUARIO=:p_usuario_id FOR UPDATE', {'p_usuario_id': id_usuario})
    carteira = cursor.fetchone()
    if carteira is None:
        raise ValueError("Carteira não encontrada para esta conta.")
    return carteira


def cadastrar(conexao, nome, email, senha):
    """Cria usuário e carteira vazia na mesma transação; retorna o ID da conta."""
    nome, email = validar_cadastro(nome, email)
    if not 4 <= len(senha) <= 128:
        raise ValueError("A senha deve ter entre 4 e 128 caracteres.")
    with transacao(conexao) as c:
        uid = inserir_id(c, '''INSERT INTO TB_USUARIO (NM_USUARIO, EMAIL, SENHA)
            VALUES (:nome,:email,:senha) RETURNING ID_USUARIO INTO :novo_id''',
            {'nome': nome, 'email': email, 'senha': senha})
        c.execute('INSERT INTO TB_CARTEIRA (ID_USUARIO) VALUES (:p_usuario_id)', {'p_usuario_id': uid})
    return uid


def autenticar(conexao, email, senha):
    """Retorna os dados públicos da conta autenticada ou None."""
    linhas = consultar(conexao, 'SELECT ID_USUARIO, NM_USUARIO, EMAIL, SENHA, SENHA_HASH FROM TB_USUARIO WHERE EMAIL=:email', {'email': email.strip().lower()})
    if linhas and ((linhas[0]['senha'] is not None and senha == linhas[0]['senha']) or
                    (linhas[0]['senha'] is None and verificar_senha(senha, linhas[0]['senha_hash']))):
        usuario = linhas[0]
        if usuario['senha'] is None:
            with transacao(conexao) as c:
                c.execute('UPDATE TB_USUARIO SET SENHA=:senha, SENHA_HASH=NULL WHERE ID_USUARIO=:p_usuario_id',
                            {'senha': senha, 'p_usuario_id': usuario['id_usuario']})
        del usuario['senha']
        del usuario['senha_hash']
        return usuario
    return None


def minha_conta(conexao, uid):
    """Consulta a conta pelo ID da sessão, sem expor o hash de senha."""
    linhas = consultar(conexao, 'SELECT ID_USUARIO, NM_USUARIO, EMAIL, DT_CADASTRO FROM TB_USUARIO WHERE ID_USUARIO=:p_usuario_id', {'p_usuario_id': uid})
    if not linhas:
        raise ValueError('Conta não encontrada.')
    return linhas[0]


def editar(conexao, uid, nome, senha=''):
    """Atualiza somente a conta da sessão; senha vazia mantém a atual."""
    nome = nome.strip()
    if not 1 <= len(nome) <= 100:
        raise ValueError('Nome obrigatório, com até 100 caracteres.')
    if senha and not 4 <= len(senha) <= 128:
        raise ValueError('A senha deve ter entre 4 e 128 caracteres.')
    with transacao(conexao) as c:
        bloquear_usuario(c, uid)
        c.execute('UPDATE TB_USUARIO SET NM_USUARIO=:nome WHERE ID_USUARIO=:p_usuario_id', {'nome': nome, 'p_usuario_id': uid})
        if senha:
            c.execute('UPDATE TB_USUARIO SET SENHA=:senha, SENHA_HASH=NULL WHERE ID_USUARIO=:p_usuario_id', {'senha': senha, 'p_usuario_id': uid})


def excluir(conexao, uid):
    """Exclui a conta e seus registros dependentes, em uma única transação."""
    with transacao(conexao) as c:
        bloquear_carteira(c, uid)
        mov = 'SELECT m.ID_MOVIMENTACAO FROM TB_MOVIMENTACAO m JOIN TB_CARTEIRA c ON c.ID_CARTEIRA=m.ID_CARTEIRA WHERE c.ID_USUARIO=:p_usuario_id'
        comprov = 'SELECT c.ID_COMPROVACAO FROM TB_COMPROVACAO c JOIN TB_PARTICIPACAO p ON p.ID_PARTICIPACAO=c.ID_PARTICIPACAO WHERE p.ID_USUARIO=:p_usuario_id'
        # Trechos SQL fixos; o ID é sempre passado como parâmetro.
        consultas = [
            'DELETE FROM TB_RESGATE WHERE ID_MOVIMENTACAO IN ('+mov+')',
            'DELETE FROM TB_MOVIMENTACAO WHERE ID_CARTEIRA IN (SELECT ID_CARTEIRA FROM TB_CARTEIRA WHERE ID_USUARIO=:p_usuario_id)',
            'DELETE FROM TB_VALIDACAO WHERE ID_COMPROVACAO IN ('+comprov+')',
            'DELETE FROM TB_COMPROVACAO WHERE ID_PARTICIPACAO IN (SELECT ID_PARTICIPACAO FROM TB_PARTICIPACAO WHERE ID_USUARIO=:p_usuario_id)',
            'DELETE FROM TB_PARTICIPACAO WHERE ID_USUARIO=:p_usuario_id',
            'DELETE FROM TB_CARTEIRA WHERE ID_USUARIO=:p_usuario_id',
            'DELETE FROM TB_USUARIO WHERE ID_USUARIO=:p_usuario_id',
        ]
        for sql in consultas:
            c.execute(sql, {'p_usuario_id': uid})


def desafios(conexao):
    """Lista os desafios ativos e suas pontuações."""
    return consultar(conexao, "SELECT ID_DESAFIO, NM_DESAFIO, DS_DESCRICAO, PONTOS_DESAFIO FROM TB_DESAFIO WHERE ST_ATIVO='S' ORDER BY ID_DESAFIO")


def registrar_atividade(conexao, uid, desafio, descricao, referencia='', aprovado=True):
    """Registra a comprovação e uma validação SIMULADA; credita somente se aprovada.

    Não analisa imagens nem envia arquivos. A referência é apenas texto.
    Retorna os pontos creditados, ou zero para uma rejeição simulada.
    """
    descricao, referencia = descricao.strip(), referencia.strip()
    if not 1 <= len(descricao) <= 500 or len(referencia) > 500:
        raise ValueError('Informe uma descrição de até 500 caracteres e referência de até 500.')
    if type(aprovado) is not bool:
        raise ValueError('Resultado de simulação inválido.')
    with transacao(conexao) as c:
        carteira, saldo = bloquear_carteira(c, uid)
        c.execute("SELECT NM_DESAFIO, PONTOS_DESAFIO FROM TB_DESAFIO WHERE ID_DESAFIO=:did AND ST_ATIVO='S'", {'did': desafio})
        dados = c.fetchone()
        if not dados:
            raise ValueError('Desafio não encontrado ou inativo.')
        nome, pontos = dados
        pid = inserir_id(c, 'INSERT INTO TB_PARTICIPACAO (ID_USUARIO,ID_DESAFIO) VALUES (:p_usuario_id,:did) RETURNING ID_PARTICIPACAO INTO :novo_id', {'p_usuario_id': uid, 'did': desafio})
        cid = inserir_id(c, 'INSERT INTO TB_COMPROVACAO (ID_PARTICIPACAO,DS_DESCRICAO,REFERENCIA_ARQUIVO) VALUES (:pid,:descricao,:referencia) RETURNING ID_COMPROVACAO INTO :novo_id', {'pid': pid,'descricao': descricao,'referencia': referencia or None})
        vid = inserir_id(c, '''INSERT INTO TB_VALIDACAO (ID_COMPROVACAO,ST_RESULTADO,METODO,OBSERVACAO)
            VALUES (:cid,:resultado,'SIMULADA','Resultado escolhido no demonstrador; sem analise real de IA.') RETURNING ID_VALIDACAO INTO :novo_id''', {'cid': cid,'resultado': 'APROVADO' if aprovado else 'REJEITADO'})
        if aprovado:
            c.execute('UPDATE TB_CARTEIRA SET SALDO_PONTOS=SALDO_PONTOS+:pontos, DT_ATUALIZACAO=SYSTIMESTAMP WHERE ID_CARTEIRA=:cid', {'pontos': pontos,'cid': carteira})
            c.execute("INSERT INTO TB_MOVIMENTACAO (ID_CARTEIRA,ID_VALIDACAO,TP_MOVIMENTACAO,VALOR,DS_DESCRICAO) VALUES (:cid,:vid,'CREDITO',:pontos,:descricao)", {'cid': carteira,'vid': vid,'pontos': pontos,'descricao': nome})
    return int(pontos) if aprovado else 0


def saldo(conexao, uid):
    """Consulta o saldo individual no Oracle."""
    linhas = consultar(conexao, 'SELECT SALDO_PONTOS FROM TB_CARTEIRA WHERE ID_USUARIO=:p_usuario_id', {'p_usuario_id': uid})
    if not linhas:
        raise ValueError('Carteira não encontrada.')
    return int(linhas[0]['saldo_pontos'])


def historico(conexao, uid, tipo=None):
    """Consulta movimentações somente da carteira do usuário autenticado."""
    sql = '''SELECT m.ID_MOVIMENTACAO,m.TP_MOVIMENTACAO,m.VALOR,m.DS_DESCRICAO,m.DT_MOVIMENTACAO
        FROM TB_MOVIMENTACAO m JOIN TB_CARTEIRA c ON c.ID_CARTEIRA=m.ID_CARTEIRA WHERE c.ID_USUARIO=:p_usuario_id'''
    parametros = {'p_usuario_id': uid}
    if tipo:
        if tipo not in ('CREDITO','RESGATE'):
            raise ValueError('Tipo inválido: use CREDITO ou RESGATE.')
        sql += ' AND m.TP_MOVIMENTACAO=:tipo'
        parametros['tipo'] = tipo
    return consultar(conexao, sql+' ORDER BY m.ID_MOVIMENTACAO', parametros)


def resgatar(conexao, uid, tipo):
    """Debita pontos e registra um benefício simulado; retorna código e custo."""
    if tipo not in CUSTOS_RESGATE:
        raise ValueError('Tipo de resgate inválido.')
    custo = CUSTOS_RESGATE[tipo]
    codigo = 'DEMO-'+uuid4().hex
    with transacao(conexao) as c:
        carteira, pontos = bloquear_carteira(c, uid)
        if pontos < custo:
            raise ValueError(f'Pontos insuficientes. Necessários: {custo}; saldo: {pontos}.')
        c.execute('UPDATE TB_CARTEIRA SET SALDO_PONTOS=SALDO_PONTOS-:custo, DT_ATUALIZACAO=SYSTIMESTAMP WHERE ID_CARTEIRA=:cid', {'custo': custo,'cid': carteira})
        mid = inserir_id(c, "INSERT INTO TB_MOVIMENTACAO (ID_CARTEIRA,TP_MOVIMENTACAO,VALOR,DS_DESCRICAO) VALUES (:cid,'RESGATE',:valor,:descricao) RETURNING ID_MOVIMENTACAO INTO :novo_id", {'cid': carteira,'valor': -custo,'descricao': 'Resgate simulado: '+tipo})
        c.execute('INSERT INTO TB_RESGATE (ID_MOVIMENTACAO,TP_BENEFICIO,PONTOS_UTILIZADOS,CODIGO) VALUES (:mid,:tipo,:custo,:codigo)', {'mid': mid,'tipo': tipo,'custo': custo,'codigo': codigo})
    return codigo, custo


def meus_resgates(conexao, uid):
    """Consulta os benefícios simulados da conta autenticada."""
    return consultar(conexao, '''SELECT r.ID_RESGATE,r.TP_BENEFICIO,r.PONTOS_UTILIZADOS,r.CODIGO,r.ST_STATUS,r.DT_RESGATE
        FROM TB_RESGATE r JOIN TB_MOVIMENTACAO m ON m.ID_MOVIMENTACAO=r.ID_MOVIMENTACAO
        JOIN TB_CARTEIRA c ON c.ID_CARTEIRA=m.ID_CARTEIRA WHERE c.ID_USUARIO=:p_usuario_id ORDER BY r.ID_RESGATE''', {'p_usuario_id': uid})


def minhas_atividades(conexao, uid):
    """Consulta participações, comprovações e resultados da conta autenticada."""
    return consultar(conexao, '''SELECT p.ID_PARTICIPACAO,d.NM_DESAFIO,c.DS_DESCRICAO,c.REFERENCIA_ARQUIVO,v.ST_RESULTADO,v.METODO
        FROM TB_PARTICIPACAO p JOIN TB_DESAFIO d ON d.ID_DESAFIO=p.ID_DESAFIO
        JOIN TB_COMPROVACAO c ON c.ID_PARTICIPACAO=p.ID_PARTICIPACAO
        JOIN TB_VALIDACAO v ON v.ID_COMPROVACAO=c.ID_COMPROVACAO
        WHERE p.ID_USUARIO=:p_usuario_id ORDER BY p.ID_PARTICIPACAO''', {'p_usuario_id': uid})
