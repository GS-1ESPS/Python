import requests                 # Biblioteca para fazer requisições HTTP (buscar dados da API)
import datetime                 # Para trabalhar com datas
import sqlite3                  # Para trabalhar com banco de dados SQLite
import matplotlib.pyplot as plt # Para gerar gráficos
import pandas as pd             # Para manipular dados em tabelas (DataFrame)
from datetime import date       # Para pegar a data atual
from geopy.geocoders import Nominatim  # Para converter CEP em coordenadas geográficas (lat/lon)


def obter_lat_lon_por_cep(cep):
    # Cria um objeto geolocator para usar o serviço Nominatim (OpenStreetMap)
    geolocator = Nominatim(user_agent="pluviometria_app")
    
    # Formata o endereço para a busca: CEP + país (Brasil)
    endereco = f"{cep}, Brazil"
    
    # Faz a busca no geolocator para obter localização
    location = geolocator.geocode(endereco)
    
    # Se encontrar a localização, retorna latitude e longitude
    if location:
        return location.latitude, location.longitude
    else:
        # Se não encontrar, avisa e retorna None para ambos
        print("Local não encontrado para o CEP:", cep)
        return None, None


def buscar_chuva(lat, lon):
    # Pega a data atual
    hoje = datetime.date.today()
    
    # Define data final como 6 dias depois da atual (para 7 dias de previsão)
    fim = hoje + datetime.timedelta(days=6)
    
    # Monta a URL da API Open-Meteo para buscar precipitação diária no período
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&daily=precipitation_sum&timezone=America/Sao_Paulo"
        f"&start_date={hoje}&end_date={fim}"
    )
    
    # Faz a requisição GET para a API
    response = requests.get(url)
    
    # Se a resposta for sucesso (código 200)
    if response.status_code == 200:
        # Retorna o JSON com os dados da previsão
        return response.json()
    else:
        # Se erro, avisa e retorna None
        print("Erro ao buscar dados da API:", response.status_code)
        return None


def gerar_grafico(dados, cep):
    # Extrai as listas de datas e de chuvas do JSON da API
    datas = dados['daily']['time']
    chuvas = dados['daily']['precipitation_sum']
    
    # Cria um DataFrame para manipular os dados com pandas
    df = pd.DataFrame({'Data': datas, 'Chuva (mm)': chuvas})
    
    # Define um nível perigoso de chuva para referência no gráfico (exemplo: 50 mm)
    nivel_perigoso = 50
    
    # Configura o tamanho do gráfico
    plt.figure(figsize=(10, 5))
    
    # Plota a linha da precipitação diária
    plt.plot(df['Data'], df['Chuva (mm)'], marker='o', label='Precipitação (mm)')
    
    # Desenha uma linha horizontal vermelha no nível perigoso
    plt.axhline(y=nivel_perigoso, color='r', linestyle='--', label='Nível perigoso (50 mm)')
    
    # Título do gráfico com o CEP
    plt.title(f"Previsão de Chuva para o CEP {cep}")
    
    # Legendas dos eixos X e Y
    plt.xlabel("Data")
    plt.ylabel("Chuva (mm)")
    
    # Rotaciona as datas para melhor visualização
    plt.xticks(rotation=45)
    
    # Adiciona a legenda com as descrições das linhas
    plt.legend()
    
    # Ajusta layout para não cortar nada no gráfico
    plt.tight_layout()
    
    # Nome do arquivo para salvar o gráfico com a data atual
    nome_arquivo = f"chuva_{cep}_{date.today()}.png"
    
    # Salva o gráfico em arquivo PNG
    plt.savefig(nome_arquivo)
    
    # Fecha o gráfico para liberar memória
    plt.close()
    
    # Mensagem informando onde o arquivo foi salvo
    print(f"Gráfico salvo como {nome_arquivo}")
    
    # Retorna o nome do arquivo gerado
    return nome_arquivo


def salvar_em_sqlite(cep, datas, chuvas):
    # Conecta (ou cria) o arquivo de banco de dados SQLite
    conn = sqlite3.connect('analise_diaria.db')
    
    # Cria um cursor para executar comandos SQL
    cursor = conn.cursor()
    
    # Cria a tabela chuva_semana caso não exista, com colunas cep, data e chuva
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chuva_semana (
            cep TEXT,
            data TEXT,
            chuva REAL
        )
    ''')
    
    # Insere as informações no banco para cada data e respectiva chuva
    for d, c in zip(datas, chuvas):
        cursor.execute('INSERT INTO chuva_semana (cep, data, chuva) VALUES (?, ?, ?)', (cep, d, c))
    
    # Salva (commit) as alterações no banco
    conn.commit()
    
    # Fecha a conexão
    conn.close()
    
    # Confirmação
    print("Dados salvos no banco.")


def principal():
    # Pede o CEP para o usuário
    cep = input("Digite o CEP: ").strip()
    
    # Obtem latitude e longitude do CEP
    lat, lon = obter_lat_lon_por_cep(cep)
    
    # Se não conseguiu obter, termina o programa
    if not lat or not lon:
        return
    
    # Busca os dados de chuva pela API
    dados_chuva = buscar_chuva(lat, lon)
    
    # Se erro ao buscar dados, termina o programa
    if not dados_chuva:
        return
    
    # Gera e salva o gráfico com os dados obtidos
    gerar_grafico(dados_chuva, cep)
    
    # Pega as listas de datas e chuva para salvar no banco
    datas = dados_chuva['daily']['time']
    chuvas = dados_chuva['daily']['precipitation_sum']
    
    # Salva as informações no banco de dados
    salvar_em_sqlite(cep, datas, chuvas)


# Este bloco garante que o main() só rode se o script for executado diretamente,
# evitando que rode se você importar esse arquivo como módulo
if __name__ == "__main__":
    principal()
