# ROTTA — Python com Oracle

## Como executar

1. Abra ROTTA_BANCO_PYTHON_COMPLETO.sql no SQL Developer, na conexão FIAP. Execute com F5 uma única vez. Espere as mensagens de oito tabelas criadas e desafios carregados. A consulta final deve listar seis desafios.
2. Se aparecer erro de objetos existentes, pare e confira quais tabelas já existem. Não execute scripts antigos nem apague tabelas automaticamente. O arquivo não substitui tabelas; criação de estrutura no Oracle não pode ser desfeita com ROLLBACK.
3. No terminal, entre na pasta que contém Rottatest.py, banco_rotta.py e requirements.txt:

```powershell
cd 'C:\Users\thiag\OneDrive\Documentos\4 sprint challenge\python - TUDO\rotta-python'
python -m pip install -r requirements.txt
python Rottatest.py
```

4. Informe usuário e senha do Oracle, os mesmos do SQL Developer. A senha fica oculta. A conexão usa oracle.fiap.com.br:1521 e SID ORCL. Também aceita ROTTA_ORACLE_USER e ROTTA_ORACLE_PASSWORD como variáveis de ambiente; não grava credenciais em arquivos.
5. No menu inicial, escolha cadastrar e crie uma conta ROTTA. O login da aplicação é separado da conexão Oracle. Contas começam com zero pontos.

Requer Python 3.10+ e Oracle 12c+ com permissão de criação de tabelas e espaço disponível.

## Estrutura

| Tabela | Uso |
|---|---|
| TB_USUARIO | Cadastro e senha original; hash apenas para contas antigas |
| TB_DESAFIO | Seis desafios iniciais e pontos por ação |
| TB_CARTEIRA | Saldo individual de cada usuário |
| TB_PARTICIPACAO | Participações nos desafios |
| TB_COMPROVACAO | Descrição digitada e referência opcional de mídia |
| TB_VALIDACAO | Resultado e método da análise demonstrativa |
| TB_MOVIMENTACAO | Créditos e débitos da carteira |
| TB_RESGATE | Benefícios demonstrativos e seus códigos |

## O que mudou

O aplicativo passa a consultar e gravar no Oracle. Cadastro e carteira são criados juntos; atividades aprovadas geram pontos e movimentação juntos; resgates debitam e registram o benefício na mesma transação. Falhas desfazem as alterações da operação. Operações de escrita bloqueiam a conta e a carteira até finalizar.

Minha conta edita e exclui somente o usuário conectado. Excluir remove também seus registros dependentes após confirmação e encerra a sessão. Consultas de saldo, atividades, cadastro e resgates são individuais. Por escolha do grupo para a demonstração acadêmica, senhas da ROTTA são digitadas visivelmente e armazenadas em texto na coluna SENHA. Contas antigas ainda usam o hash até o primeiro login correto, quando a senha informada é salva na coluna SENHA e o hash é removido. O catálogo de desafios é compartilhado.

A opção 9 exporta consultas do Oracle para exportacoes/consultas_usuario_ID_DATA.json, sem hash de senha. As operações de cadastro, leitura e edição desta execução também podem constar no arquivo. A exclusão encerra o acesso e seu registro em memória não gera uma exportação automática; exporte as consultas antes de excluir.

Os JSON antigos ficam preservados, mas não são utilizados nem migrados automaticamente: saldo e histórico antigos não identificavam de forma confiável o proprietário. O banco começa com desafios, sem contas de exemplo.

## Regras demonstrativas e limites

- Pontos agora variam por desafio: 15, 20, 40, 25, 30 e 20. A versão anterior creditava 50 por atividade.
- Passagem: 100 pontos; QR Code: 150; cartão: 100. São parâmetros acadêmicos, sem equivalência financeira real. O custo de cartão é uma regra demonstrativa desta integração.
- O usuário digita o que fez e escolhe aprovação ou rejeição na simulação. O resultado é gravado com método SIMULADA. Não há análise real por IA, upload de mídia ou proteção contra repetição da mesma comprovação.
- QR Codes contêm códigos DEMO únicos, sem validade em catracas. Resgates não enviam dinheiro nem créditos a operadoras.
- A Capi permanece sem integração. A API pública de clima está integrada; a análise real de mídias ainda precisa ser desenvolvida.
- O projeto possui versão de terminal (Rottatest.py) e interface web local (app_web.py), ambas usando o mesmo Oracle. Veja GUIA_WEB.md. Vídeo e documentação final ainda fazem parte da entrega da Sprint 4.

## Roteiro para conferir na sua conexão

Cadastre duas contas. Entre na primeira, registre uma ação aprovada e uma rejeitada; somente a aprovada deve pontuar. Registre ações até acumular pontos, confirme um resgate e confira o histórico. Exporte o JSON. Entre na segunda conta e confira que saldo e histórico não incluem dados da primeira. Edite e, se desejar testar exclusão, exclua somente uma conta de teste.

## Validação realizada

Oito testes automatizados locais passaram: autenticação/edição, e-mail duplicado, aprovação/rejeição, resgate, rollback de cadastro/crédito, rollback de resgate, exclusão isolada e exportação JSON. Os testes usam SQLite em memória com adaptação das chamadas Oracle. Eles verificam a lógica e as transações, mas não comprovam sintaxe PL/SQL, bloqueios concorrentes ou conectividade do Oracle real. Os arquivos Python também passaram pela verificação de sintaxe.

## Alteração de senha para banco já criado
Execute somente ROTTA_AJUSTAR_SENHA.sql com F5, depois reinicie o Python. Não execute novamente o script de criação. Consulte SELECT ID_USUARIO, NM_USUARIO, EMAIL, SENHA FROM TB_USUARIO; para ver as senhas. A senha da conexão Oracle continua oculta.

## API pública — clima para o deslocamento

Após o login, escolha 5 — Clima para o deslocamento. Digite uma cidade brasileira e selecione a cidade/estado na lista. A ROTTA consulta a Open-Meteo por HTTPS e mostra temperatura em °C, precipitação em mm, vento em km/h, horário local e fonte dos dados. A sugestão de transporte é uma regra simples baseada na precipitação retornada, não uma análise por IA nem garantia de segurança do trajeto.

A função ajuda a planejar deslocamentos sustentáveis: caminhada, bicicleta ou transporte público. Não credita pontos, não comprova ações e não altera o Oracle. O programa envia à API somente o nome da cidade e, na consulta meteorológica, coordenadas públicas e parâmetros do clima. Não envia cadastro nem senha.

A consulta bem-sucedida fica nas operações da sessão da conta atual. Escolha 9 para exportá-la em JSON junto dos dados do usuário. Se encerrar o programa antes da exportação, a consulta de clima não é preservada. Sem internet ou com dados incompletos, o programa informa a falha e retorna ao menu; não inventa dados. Cada requisição possui timeout de 10 segundos.

Usa apenas a biblioteca padrão Python (urllib e json), sem dependência ou chave adicional para este uso acadêmico não comercial. Fonte e documentação: https://open-meteo.com/en/docs e https://open-meteo.com/en/docs/geocoding-api. Para uso comercial, conferir as condições do serviço.

### Como demonstrar no vídeo
Abra a opção 5, procure a cidade e explique as duas requisições GET: busca das coordenadas e consulta meteorológica. Mostre o resultado, a dica baseada na precipitação e o tratamento de erros. Exporte pela opção 9 e mostre a entrada consulta_api_clima no JSON. Explique que os valores vêm da API e não são fixos no código.

## Interface web
A interface Flask foi adicionada. Instale requirements.txt atualizado e execute python app_web.py. Consulte GUIA_WEB.md para acesso e demonstração da integração nos dois sentidos.
