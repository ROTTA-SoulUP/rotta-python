"""Interface web local da ROTTA. Execute: python app_web.py."""
import io
import json
import os
import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import wraps
from getpass import getpass

import oracledb
from flask import Flask, abort, flash, g, redirect, render_template, request, send_file, session, url_for
import banco_rotta as banco
import api_clima


def criar_app(config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get('ROTTA_WEB_SECRET') or secrets.token_hex(32),
                      MAX_CONTENT_LENGTH=32 * 1024, SESSION_COOKIE_HTTPONLY=True,
                        SESSION_COOKIE_SAMESITE='Lax', PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
                        ORACLE_USER=os.environ.get('ROTTA_ORACLE_USER'),
                        ORACLE_PASSWORD=os.environ.get('ROTTA_ORACLE_PASSWORD'))
    if config:
        app.config.update(config)

    def conectar():
        # Uma conexão por requisição: nunca compartilha transações entre usuários.
        if 'db' not in g:
            if app.config.get('DB_FACTORY'):
                g.db = app.config['DB_FACTORY']()
            else:
                if not app.config['ORACLE_USER'] or not app.config['ORACLE_PASSWORD']:
                    raise ValueError('Inicie com python app_web.py e informe a conexão Oracle no terminal.')
                params = oracledb.ConnectParams(host='oracle.fiap.com.br', port=1521, sid='ORCL', tcp_connect_timeout=10, retry_count=0)
                g.db = oracledb.connect(user=app.config['ORACLE_USER'], password=app.config['ORACLE_PASSWORD'], params=params)
                g.db.call_timeout = 20000
        return g.db

    @app.teardown_appcontext
    def fechar_conexao(erro):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    @app.before_request
    def preparar():
        session.setdefault('csrf', secrets.token_urlsafe(32))
        if request.method == 'POST':
            token = request.form.get('csrf', '')
            if not secrets.compare_digest(token, session['csrf']):
                abort(400, description='Formulário expirado. Atualize a página e tente novamente.')

    @app.after_request
    def evitar_cache(resposta):
        if request.endpoint != 'static':
            resposta.headers['Cache-Control'] = 'no-store'
        resposta.headers['X-Content-Type-Options'] = 'nosniff'
        return resposta

    def autenticado(funcao):
        @wraps(funcao)
        def interna(*args, **kwargs):
            if not session.get('uid'):
                return redirect(url_for('login'))
            # Detecta também contas excluídas pelo terminal.
            try:
                g.usuario = banco.minha_conta(conectar(), session['uid'])
            except ValueError:
                session.clear()
                flash('Sua conta não está disponível. Entre novamente.', 'erro')
                return redirect(url_for('login'))
            return funcao(*args, **kwargs)
        return interna

    @app.context_processor
    def contexto():
        return {'usuario': getattr(g, 'usuario', None)}

    @app.errorhandler(ValueError)
    def entrada_invalida(erro):
        return render_template('erro.html', mensagem=str(erro)), 400

    @app.errorhandler(oracledb.Error)
    def erro_oracle(erro):
        codigo = getattr(erro.args[0], 'code', None) if erro.args else None
        mensagem = 'Este e-mail já está cadastrado.' if codigo == 1 else 'Não foi possível acessar o Oracle. Confira a conexão e tente novamente.'
        return render_template('erro.html', mensagem=mensagem), 409 if codigo == 1 else 503

    @app.errorhandler(400)
    def erro_formulario(erro):
        return render_template('erro.html', mensagem=erro.description), 400

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user = banco.autenticar(conectar(), request.form.get('email', ''), request.form.get('senha', ''))
            if not user:
                flash('E-mail ou senha incorretos.', 'erro')
                return render_template('acesso.html', cadastro=False), 401
            session.clear()
            session.update(uid=int(user['id_usuario']), csrf=secrets.token_urlsafe(32))
            session.permanent = True
            return redirect(url_for('inicio'))
        return render_template('acesso.html', cadastro=False)

    @app.route('/cadastro', methods=['GET', 'POST'])
    def cadastro():
        if request.method == 'POST':
            senha = request.form.get('senha', '')
            if senha != request.form.get('confirmacao', ''):
                raise ValueError('As senhas não conferem.')
            banco.cadastrar(conectar(), request.form.get('nome', ''), request.form.get('email', ''), senha)
            flash('Conta criada! Entre com seu e-mail e senha.', 'sucesso')
            return redirect(url_for('login'))
        return render_template('acesso.html', cadastro=True)

    @app.post('/sair')
    def sair():
        session.clear()
        return redirect(url_for('login'))

    @app.get('/')
    @autenticado
    def inicio():
        db, uid = conectar(), session['uid']
        return render_template('inicio.html', saldo=banco.saldo(db, uid), desafios=banco.desafios(db),
                                movimentos=banco.historico(db, uid)[-5:][::-1], custos=banco.CUSTOS_RESGATE)

    @app.post('/atividade')
    @autenticado
    def atividade():
        resultado = request.form.get('resultado')
        if resultado not in ('APROVADO', 'REJEITADO'):
            raise ValueError('Escolha o resultado da simulação.')
        pontos = banco.registrar_atividade(conectar(), session['uid'], int(request.form.get('desafio', '0')),
                    request.form.get('descricao', ''), request.form.get('referencia', ''), resultado == 'APROVADO')
        flash(f'Atividade registrada. Resultado simulado: {resultado.lower()}. +{pontos} pontos.', 'sucesso')
        return redirect(url_for('historico'))

    @app.post('/resgate')
    @autenticado
    def resgate():
        if request.form.get('confirmar') != 'sim':
            raise ValueError('Confirme o resgate antes de continuar.')
        codigo, custo = banco.resgatar(conectar(), session['uid'], request.form.get('tipo', ''))
        flash(f'Resgate demonstrativo registrado. {custo} pontos debitados.', 'sucesso')
        return redirect(url_for('historico'))

    @app.get('/historico')
    @autenticado
    def historico():
        db, uid = conectar(), session['uid']
        return render_template('historico.html', movimentos=banco.historico(db, uid, request.args.get('tipo') or None)[::-1],
                                atividades=banco.minhas_atividades(db, uid)[::-1], resgates=banco.meus_resgates(db, uid)[::-1])

    @app.get('/qr/<int:resgate_id>')
    @autenticado
    def qr(resgate_id):
        item = next((r for r in banco.meus_resgates(conectar(), session['uid']) if r['id_resgate'] == resgate_id and r['tp_beneficio'] == 'QRCODE'), None)
        if not item:
            abort(404)
        import qrcode
        import qrcode.image.svg
        imagem = qrcode.make(item['codigo'], image_factory=qrcode.image.svg.SvgPathImage)
        buffer = io.BytesIO()
        imagem.save(buffer)
        buffer.seek(0)
        return send_file(buffer, mimetype='image/svg+xml')

    @app.route('/conta', methods=['GET', 'POST'])
    @autenticado
    def conta():
        if request.method == 'POST':
            banco.editar(conectar(), session['uid'], request.form.get('nome', ''), request.form.get('senha', ''))
            flash('Cadastro atualizado no Oracle.', 'sucesso')
            return redirect(url_for('conta'))
        return render_template('conta.html')

    @app.post('/conta/excluir')
    @autenticado
    def excluir():
        if request.form.get('confirmacao') != 'EXCLUIR':
            raise ValueError('Digite EXCLUIR para confirmar a exclusão da sua conta.')
        banco.excluir(conectar(), session['uid'])
        session.clear()
        flash('Sua conta e seus registros foram excluídos.', 'sucesso')
        return redirect(url_for('login'))

    @app.route('/clima', methods=['GET', 'POST'])
    @autenticado
    def clima():
        if request.method == 'POST':
            if request.form.get('acao') == 'buscar':
                session['cidades'] = api_clima.buscar_cidades(request.form.get('cidade', ''))
                session.pop('clima', None)
                if not session['cidades']:
                    flash('Cidade não encontrada. Tente outro nome.', 'erro')
            elif request.form.get('acao') == 'consultar':
                cidades = session.get('cidades', [])
                indice = int(request.form.get('indice', '-1'))
                if not 0 <= indice < len(cidades):
                    raise ValueError('Busque e selecione uma cidade na lista.')
                session['clima'] = api_clima.consultar_clima(cidades[indice])
            else:
                raise ValueError('Consulta inválida.')
            return redirect(url_for('clima'))
        return render_template('clima.html', cidades=session.get('cidades', []), clima=session.get('clima'))

    @app.get('/exportar')
    @autenticado
    def exportar():
        db, uid = conectar(), session['uid']
        dados = {'usuario': banco.minha_conta(db, uid), 'saldo_pontos': banco.saldo(db, uid),
                    'atividades': banco.minhas_atividades(db, uid), 'movimentacoes': banco.historico(db, uid),
                    'resgates': banco.meus_resgates(db, uid), 'ultima_consulta_clima': session.get('clima')}
        def serializar(valor):
            if isinstance(valor, (date, datetime)):
                return valor.isoformat()
            if isinstance(valor, Decimal):
                return int(valor) if valor == valor.to_integral_value() else str(valor)
            raise TypeError('Tipo não serializável')
        arquivo = io.BytesIO(json.dumps(dados, ensure_ascii=False, indent=2, default=serializar).encode('utf-8'))
        return send_file(arquivo, mimetype='application/json', as_attachment=True, download_name=f'rotta_usuario_{uid}.json')

    return app


if __name__ == '__main__':
    usuario = os.environ.get('ROTTA_ORACLE_USER') or input('Usuário Oracle (FIAP): ').strip()
    senha = os.environ.get('ROTTA_ORACLE_PASSWORD') or getpass('Senha Oracle: ')
    if not usuario or not senha:
        print('Informe usuário e senha do Oracle para iniciar.')
    else:
        app = criar_app({'ORACLE_USER': usuario, 'ORACLE_PASSWORD': senha})
        print('ROTTA Web: abra http://127.0.0.1:5000 no navegador. Ctrl+C encerra.')
        app.run(host='127.0.0.1', port=5000, debug=False)
