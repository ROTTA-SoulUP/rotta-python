# ROTTA Web — Python, Flask e Oracle

## Iniciar

No terminal do VS Code:

```powershell
cd "C:\Users\thiag\OneDrive\Documentos\4 sprint challenge\python - TUDO\rotta-python"
python -m pip install -r requirements.txt
python app_web.py
```

Informe as credenciais Oracle no terminal. Abra http://127.0.0.1:5000 no navegador e entre com a conta ROTTA que você já utiliza no terminal. Mantenha o terminal aberto; Ctrl+C encerra o servidor. Não é necessário recriar tabelas.

O servidor é local: não publica o site na internet. A senha Oracle fica somente no processo Python, nunca nas páginas ou no cookie. As senhas ROTTA seguem a regra acadêmica já escolhida pelo grupo: entrada visível e coluna SENHA. O navegador não recebe listas de senhas.

## Telas

- Cadastro e login com as contas existentes no Oracle.
- Minha carteira: saldo, atividades e resgates demonstrativos.
- Histórico: créditos, débitos, comprovações, validações e resgates da própria conta.
- QR Code: imagem do código demonstrativo de resgate, sem validade no transporte.
- Minha conta: consultar nome/e-mail, editar nome/senha e excluir a própria conta com confirmação explícita.
- Clima: busca de cidade e consulta real à Open-Meteo.
- Exportar JSON: download dos dados da conta e da última consulta de clima da sessão web.

## Integração nos dois sentidos

O navegador envia formulários às rotas Flask de app_web.py. Essas rotas chamam banco_rotta.py, o mesmo módulo usado por Rottatest.py. Cada requisição abre e fecha sua própria conexão Oracle. O aplicativo do terminal permanece funcionando.

Exemplo para o vídeo: entre na mesma conta no terminal e na web. Registre uma atividade pelo terminal; atualize a página web (F5) e confira o saldo/histórico. Registre outra atividade pela web; consulte novamente o saldo no terminal. Edite o nome pela web e consulte o cadastro no terminal. Não há atualização automática em tempo real: use F5 ou navegue para consultar novamente.

A conta sempre é obtida da sessão autenticada, nunca de um ID enviado pelo formulário. Escritas são POST e usam token de formulário. Exclusão e resgate exigem confirmação. As transações continuam no módulo banco_rotta.py.

## Arquivos

- app_web.py: fábrica Flask, conexão por requisição, sessões, rotas e download JSON.
- templates/: páginas HTML renderizadas pelo Python com Jinja.
- static/web.css: identidade verde e creme, com layout adaptado a telas pequenas.
- banco_rotta.py e api_clima.py: funções compartilhadas, sem duplicar as regras.
- Rottatest.py: versão do terminal, preservada.

As validações de ações e os benefícios continuam simulados; não há upload/análise de fotos, IA real, integração com catraca ou transferência de créditos reais. O clima não comprova uma atividade. Dados da API ficam na sessão web até sair/expirar; exporte para preservá-los. As sessões do navegador são encerradas ao reiniciar o servidor se não houver ROTTA_WEB_SECRET configurada.

## Validação

Oito testes automatizados das rotas passaram com o módulo de banco real sobre um adaptador SQLite de teste: autenticação/token, cadastro, dados nos dois sentidos, edição/exclusão isolada, resgate/QR por proprietário, clima/exportação, conta excluída no terminal e validação de entradas/escape HTML. Isso não substitui um teste da conexão Oracle da interface web com suas credenciais.

Também foram verificados login e navegação no navegador Edge e o layout em 1440 px e 390 px. O banco usado nessa revisão visual era temporário, com dados fictícios. Nenhum desses usuários foi criado no seu Oracle.

Documentação do framework: https://flask.palletsprojects.com/en/stable/quickstart/
Fonte da API de clima: https://open-meteo.com/en/docs
