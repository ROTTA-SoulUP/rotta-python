"""Consulta pública Open-Meteo para planejar deslocamentos da ROTTA."""
import json
import math
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError

GEOCODIFICACAO = 'https://geocoding-api.open-meteo.com/v1/search'
PREVISAO = 'https://api.open-meteo.com/v1/forecast'


def consultar_json(endpoint, parametros):
    """Faz uma requisição GET HTTPS com limite de espera e valida o JSON."""
    url = endpoint + '?' + urlencode(parametros)
    try:
        requisicao = Request(url, headers={'User-Agent': 'ROTTA-Academico/1.0'})
        with urlopen(requisicao, timeout=10) as resposta:
            dados = json.loads(resposta.read(1_000_000).decode('utf-8'))
    except (URLError, OSError, ValueError) as erro:
        raise ValueError('Não foi possível consultar o clima. Confira a internet e tente novamente.') from erro
    if not isinstance(dados, dict) or dados.get('error'):
        raise ValueError('O serviço de clima retornou uma resposta inválida. Tente novamente depois.')
    return dados


def numero_valido(valor):
    return type(valor) in (int, float) and math.isfinite(valor)


def buscar_cidades(nome):
    """Busca até cinco cidades brasileiras para o usuário escolher a correta."""
    nome = nome.strip()
    if not 2 <= len(nome) <= 100:
        raise ValueError('Digite um nome de cidade com 2 a 100 caracteres.')
    dados = consultar_json(GEOCODIFICACAO, {'name': nome, 'count': 5, 'language': 'pt', 'format': 'json', 'countryCode': 'BR'})
    cidades = dados.get('results', [])
    if not isinstance(cidades, list):
        raise ValueError('A lista de cidades recebida é inválida.')
    resultado = []
    for cidade in cidades:
        if (isinstance(cidade, dict) and cidade.get('country_code') == 'BR'
                and isinstance(cidade.get('name'), str)
                and numero_valido(cidade.get('latitude')) and numero_valido(cidade.get('longitude'))):
            resultado.append({'nome': cidade['name'], 'estado': cidade.get('admin1', ''),
                                'latitude': cidade['latitude'], 'longitude': cidade['longitude']})
    return resultado


def consultar_clima(cidade):
    """Retorna condições atuais estimadas pelo modelo meteorológico, sem acessar contas."""
    lat, lon = cidade['latitude'], cidade['longitude']
    if not numero_valido(lat) or not numero_valido(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError('Coordenadas da cidade inválidas.')
    dados = consultar_json(PREVISAO, {'latitude': lat, 'longitude': lon,
        'current': 'temperature_2m,precipitation,wind_speed_10m',
        'temperature_unit': 'celsius', 'wind_speed_unit': 'kmh', 'precipitation_unit': 'mm', 'timezone': 'auto'})
    atual = dados.get('current')
    if not isinstance(atual, dict) or not isinstance(atual.get('time'), str):
        raise ValueError('O serviço não retornou as condições atuais.')
    campos = ('temperature_2m', 'precipitation', 'wind_speed_10m')
    if not all(numero_valido(atual.get(campo)) for campo in campos):
        raise ValueError('Os dados meteorológicos estão incompletos. Tente novamente depois.')
    if atual['precipitation'] < 0 or atual['wind_speed_10m'] < 0:
        raise ValueError('O serviço retornou valores meteorológicos inválidos.')
    if atual['precipitation'] > 0:
        dica = 'Há precipitação estimada. Considere o transporte público para o trajeto.'
    else:
        dica = 'Sem precipitação estimada neste horário. Avalie caminhar ou pedalar em trajetos adequados.'
    return {'cidade': cidade['nome'], 'estado': cidade['estado'], 'horario_local': atual['time'],
            'fuso': dados.get('timezone', 'local'), 'temperatura_c': atual['temperature_2m'],
            'precipitacao_mm': atual['precipitation'], 'vento_kmh': atual['wind_speed_10m'],
            'dica': dica, 'fonte': 'Open-Meteo', 'url_fonte': 'https://open-meteo.com/'}


def menu_clima(registros):
    """Consulta real no terminal e inclui o resultado na exportação da sessão."""
    print('\nCLIMA PARA O DESLOCAMENTO — Open-Meteo')
    nome = input('Cidade brasileira (Enter para voltar): ').strip()
    if not nome:
        return
    cidades = buscar_cidades(nome)
    if not cidades:
        print('Nenhuma cidade encontrada. Confira o nome e tente novamente.')
        return
    for indice, cidade in enumerate(cidades, 1):
        print(f"{indice} - {cidade['nome']} / {cidade['estado']}")
    opcao = input('Número da cidade (0 para voltar): ').strip()
    if opcao == '0':
        return
    if not opcao.isdecimal() or not 1 <= int(opcao) <= len(cidades):
        raise ValueError('Escolha um dos números apresentados.')
    clima = consultar_clima(cidades[int(opcao)-1])
    print(f"\n{clima['cidade']} / {clima['estado']} — {clima['horario_local']} ({clima['fuso']})")
    print(f"Temperatura: {clima['temperatura_c']} °C | Precipitação: {clima['precipitacao_mm']} mm | Vento: {clima['vento_kmh']} km/h")
    print(clima['dica'])
    print('Estimativas meteorológicas; confira as condições locais antes de sair.')
    print('Fonte: Open-Meteo — https://open-meteo.com/')
    registros.append({'operacao': 'consulta_api_clima', 'dados': clima})
    print('Consulta incluída na sessão. Use a opção 9 para exportá-la em JSON.')
