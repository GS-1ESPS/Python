import requests  # Para fazer requisições HTTP à API meteorológica
import pandas as pd  # Para manipulação e análise dos dados em tabelas (DataFrames)
import matplotlib.pyplot as plt  # Para criar gráficos
from datetime import datetime, timedelta  # Para manipular datas
from geopy.geocoders import Nominatim  # Para converter CEP em latitude e longitude
import sqlite3  # Para manipular banco de dados SQLite (local)

# Função que converte CEP em latitude e longitude usando o Nominatim (OpenStreetMap)
def obter_lat_lon_por_cep(cep):
    geolocator = Nominatim(user_agent="pluviometria_app")  # Cria o objeto para busca geográfica
    endereco = f"{cep}, Brazil"  # Formata o endereço para busca no Brasil
    location = geolocator.geocode(endereco)  # Busca a localização
    if location:
        return location.latitude, location.longitude  # Retorna lat e lon se encontrado
    else:
        print("Local não encontrado para o CEP:", cep)  # Mensagem caso não encontre
        return None, None  # Retorna None se falhar

# Função que obtém a precipitação diária de uma coordenada para um mês/ano específicos
def obter_precipitacao_diaria(lat, lon, ano, mes):
    data_inicio = f"{ano}-{mes:02d}-01"  # Primeiro dia do mês
    if mes == 12:
        data_fim = f"{ano+1}-01-01"  # Se for dezembro, o fim é o início do próximo ano
    else:
        data_fim = f"{ano}-{mes+1:02d}-01"  # Senão, o primeiro dia do próximo mês

    # URL da API Open-Meteo com parâmetros: latitude, longitude, datas e tipo de dado
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={data_inicio}&end_date={data_fim}"
        f"&daily=precipitation_sum&timezone=America/Sao_Paulo"
    )
    
    resposta = requests.get(url)  # Faz a requisição GET à API
    dados = resposta.json()  # Converte a resposta em JSON (dicionário)

    # Verifica se a resposta contém os dados esperados
    if "daily" not in dados or "time" not in dados["daily"]:
        print("Erro ao obter dados meteorológicos.")
        return pd.DataFrame(columns=["date", "precipitation"])  # Retorna DataFrame vazio

    datas = dados["daily"]["time"]  # Lista de datas
    precipitacao = dados["daily"]["precipitation_sum"]  # Lista de precipitação diária
    df = pd.DataFrame({"date": pd.to_datetime(datas), "precipitation": precipitacao})  # Cria DataFrame
    df = df[df["date"].dt.month == mes]  # Filtra só as datas do mês solicitado
    return df  # Retorna DataFrame com dados diários

# Função que agrega os dados diários em soma semanal
def agregar_por_semanas(df):
    if df.empty:
        return df  # Se DataFrame vazio, retorna ele mesmo
    primeira_data = df["date"].min()  # Pega a data mais antiga (início do mês)
    # Cria coluna com o número da semana (começando em 1)
    df["week_num"] = ((df["date"] - primeira_data).dt.days // 7) + 1
    # Agrupa por semana e soma a precipitação da semana
    semanal = df.groupby("week_num")["precipitation"].sum().reset_index()
    return semanal  # Retorna DataFrame semanal

# Função que cria gráfico de barras da precipitação semanal
def criar_grafico(df_semanal, mes, ano, cep):
    if df_semanal.empty:
        print("Sem dados para plotar.")
        return
    plt.bar(df_semanal["week_num"], df_semanal["precipitation"], color="skyblue")  # Barra
    plt.xlabel("Semana do mês")  # Label eixo X
    plt.ylabel("Precipitação acumulada (mm)")  # Label eixo Y
    plt.title(f"Precipitação mensal em {mes:02d}/{ano} - CEP {cep}")  # Título do gráfico
    plt.xticks(df_semanal["week_num"])  # Mostrar os números das semanas no eixo X
    plt.grid(axis='y')  # Grid horizontal para facilitar leitura
    plt.show()  # Exibe o gráfico

#Cria a tabela no banco SQLite, se não existir
def criar_tabela_sqlite(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS precipitacao_mensal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        cep TEXT,                             
        ano INTEGER,                         
        mes INTEGER,                         
        semana INTEGER,                      
        precipitacao_mm REAL,               
        latitude REAL,                     
        longitude REAL                     
    );
    """
    conn.execute(sql)  # Executa o comando SQL
    conn.commit()  # Confirma a transação

#Salva os dados semanais no banco SQLite
def salvar_dados_sqlite(conn, cep, ano, mes, lat, lon, df_semanal):
    for _, row in df_semanal.iterrows():  # Para cada linha do DataFrame semanal
        semana = int(row["week_num"])  # Número da semana
        precipitacao = float(row["precipitation"])  # Precipitação da semana
        # Insere uma linha na tabela com todos os dados
        conn.execute(
            "INSERT INTO precipitacao_mensal (cep, ano, mes, semana, precipitacao_mm, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (cep, ano, mes, semana, precipitacao, lat, lon)
        )
    conn.commit()  # Salva as mudanças no banco

# Função principal que executa tudo
def principal():
    cep = input("Digite o CEP (formato XXXXX-XXX): ")  # Entrada do CEP
    ano = int(input("Digite o ano (ex: 2023): "))  # Entrada do ano
    mes = int(input("Digite o mês (1 a 12): "))  # Entrada do mês
    
    lat, lon = obter_lat_lon_por_cep(cep)  # Converte CEP em lat/lon
    if lat is None or lon is None:  # Se não encontrou, avisa e para execução
        print("Não foi possível obter latitude e longitude para o CEP informado.")
        return
    print(f"Latitude: {lat}, Longitude: {lon}")  # Mostra lat/lon para o usuário
    
    df_chuva = obter_precipitacao_diaria(lat, lon, ano, mes)  # Pega dados diários da chuva
    df_semanal = agregar_por_semanas(df_chuva)  # Agrega por semanas
    
    # Abre conexão com banco SQLite local (arquivo .db)
    conn = sqlite3.connect("analise_mensal.db")
    criar_tabela_sqlite(conn)  # Cria a tabela se não existir
    
    salvar_dados_sqlite(conn, cep, ano, mes, lat, lon, df_semanal)  # Salva os dados no banco
    
    criar_grafico(df_semanal, mes, ano, cep)  # Plota o gráfico
    
    conn.close()  # Fecha conexão com o banco

# Executa o programa só se for o script principal
if __name__ == "__main__":
    principal()

