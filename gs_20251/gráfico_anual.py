# Importa bibliotecas necessárias
import requests  # Para fazer requisições HTTP à API de clima
import pandas as pd  # Para manipular dados em formato de tabela
import matplotlib.pyplot as plt  # Para gerar gráficos
from datetime import datetime  # Para trabalhar com datas
from geopy.geocoders import Nominatim  # Para converter endereços (CEP) em coordenadas geográficas
import sqlite3  # Para interagir com bancos de dados SQLite
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError  # Exceções específicas do geopy
import sys  # Para acessar funcionalidades do sistema (ex: sair do programa)

# Função para obter latitude e longitude a partir de um CEP
def obter_lat_lon_por_cep(cep):
    try:
        # Cria um geolocalizador com um nome de aplicativo (requerido pela API Nominatim)
        geolocator = Nominatim(user_agent="pluviometria_app")
        
        # Formata o endereço com o CEP e país
        endereco = f"{cep}, Brazil"
        
        try:
            # Tenta geocodificar o CEP (com timeout de 10 segundos)
            location = geolocator.geocode(endereco, timeout=10)
            
            # Se encontrou localização, retorna as coordenadas
            if location:
                return location.latitude, location.longitude
            else:
                # Se não encontrou, imprime mensagem de erro
                print(f"\nErro: CEP {cep} não encontrado ou formato inválido.")
                return None, None
                
        # Trata erros específicos do serviço de geolocalização
        except (GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError) as e:
            print(f"\nErro no serviço de geolocalização: {str(e)}")
            return None, None
            
    # Trata outros erros inesperados
    except Exception as e:
        print(f"\nErro inesperado ao geocodificar CEP: {str(e)}")
        return None, None

# Função para obter dados de precipitação de uma API meteorológica
def obter_precipitacao_anual(lat, lon, ano):
    try:
        # Define o intervalo de datas para o ano solicitado
        data_inicio = f"{ano}-01-01"
        data_fim = f"{ano}-12-31"  # Apenas o ano solicitado

        # Monta a URL da API com os parâmetros necessários
        url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={lat}&longitude={lon}"
            f"&start_date={data_inicio}&end_date={data_fim}"
            f"&daily=precipitation_sum&timezone=America/Sao_Paulo"
        )
        
        # Faz a requisição HTTP com timeout de 15 segundos
        resposta = requests.get(url, timeout=15)
        resposta.raise_for_status()  # Levanta exceção se o status HTTP for ruim (4xx/5xx)
        
        # Converte a resposta para JSON
        dados = resposta.json()

        # Verifica se a resposta contém dados diários
        if not dados.get("daily"):
            print("\nAviso: Nenhum dado meteorológico disponível para este local/período.")
            return pd.DataFrame(columns=["date", "precipitation"])

        # Extrai as datas e valores de precipitação
        datas = dados["daily"]["time"]
        precipitacao = dados["daily"]["precipitation_sum"]

        # Cria um DataFrame pandas com os dados
        df = pd.DataFrame({"date": pd.to_datetime(datas), "precipitation": precipitacao})
        
        # Filtra apenas dados do ano solicitado (para garantir)
        df = df[df["date"].dt.year == ano]
        
        # Se o DataFrame estiver vazio após filtragem
        if df.empty:
            print("\nAviso: Dados meteorológicos vazios após filtragem.")
            
        return df

    # Trata erros de requisição HTTP
    except requests.exceptions.RequestException as e:
        print(f"\nErro na requisição à API meteorológica: {str(e)}")
        return pd.DataFrame(columns=["date", "precipitation"])
        
    # Trata outros erros inesperados
    except Exception as e:
        print(f"\nErro inesperado ao obter dados meteorológicos: {str(e)}")
        return pd.DataFrame(columns=["date", "precipitation"])

# Função para agregar dados diários em mensais
def agregar_por_meses(df):
    # Se o DataFrame estiver vazio, retorna sem fazer nada
    if df.empty:
        return df
        
    # Adiciona coluna com o mês extraído da data
    df["month"] = df["date"].dt.month
    
    # Agrupa por mês e soma a precipitação
    mensal = df.groupby("month")["precipitation"].sum().reset_index()
    
    return mensal

# Função para criar o gráfico de precipitação mensal
def plotar_grafico_mensal(df_mensal, ano, cep):
    # Se não houver dados, não plota
    if df_mensal.empty:
        print("\nSem dados para plotar.")
        return

    # Nomes dos meses para o eixo X
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", 
             "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    
    # Cria gráfico de barras
    plt.bar(df_mensal["month"], df_mensal["precipitation"], color="skyblue")
    
    # Configura rótulos e título
    plt.xlabel("Mês")
    plt.ylabel("Precipitação acumulada (mm)")
    plt.title(f"Precipitação anual em {ano} - CEP {cep}")
    
    # Define os ticks do eixo X com os nomes dos meses
    plt.xticks(df_mensal["month"], [meses[m-1] for m in df_mensal["month"]])
    
    # Adiciona linhas de grade horizontais
    plt.grid(axis='y')
    
    # Mostra o gráfico
    plt.show()

# Função para criar a tabela no banco de dados SQLite
def criar_tabela_sqlite_anual(conn):
    # SQL para criar tabela (se não existir)
    sql = """
    CREATE TABLE IF NOT EXISTS precipitacao_anual (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Chave primária autoincrementável
        cep TEXT,                             -- CEP da localização
        ano INTEGER,                          -- Ano da análise
        mes INTEGER,                          -- Mês (1-12)
        precipitacao_mm REAL,                 -- Precipitação em milímetros
        latitude REAL,                        -- Coordenada geográfica
        longitude REAL                        -- Coordenada geográfica
    );
    """
    # Executa o SQL e confirma a transação
    conn.execute(sql)
    conn.commit()

# Função para salvar dados no banco SQLite
def salvar_dados_sqlite_anual(conn, cep, ano, lat, lon, df_mensal):
    # Itera sobre cada linha do DataFrame
    for _, row in df_mensal.iterrows():
        mes = int(row["month"])
        precipitacao = float(row["precipitation"])
        
        # Insere os dados no banco
        conn.execute(
            "INSERT INTO precipitacao_anual (cep, ano, mes, precipitacao_mm, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)",
            (cep, ano, mes, precipitacao, lat, lon)
        )
    # Confirma todas as inserções
    conn.commit()

# Função principal que executa todo o processo
def pricip_anual():
    try:
        # Solicita entrada do usuário
        cep = input("Digite o CEP (formato XXXXX-XXX): ").strip()
        
        # Validação básica do CEP
        if not cep or len(cep.replace('-','')) != 8:
            print("\nErro: Formato de CEP inválido. Use XXXXX-XXX ou XXXXXXXX.")
            return

        try:
            # Solicita e valida o ano
            ano = int(input("Digite o ano (ex: 2023): "))
            if ano < 1900 or ano > datetime.now().year:
                print(f"\nErro: Ano deve estar entre 1900 e {datetime.now().year}.")
                return
        except ValueError:
            print("\nErro: Ano deve ser um número inteiro válido.")
            return

        # Obtém coordenadas geográficas
        lat, lon = obter_lat_lon_por_cep(cep)
        if lat is None or lon is None:
            return

        # Obtém dados de precipitação
        df_chuva = obter_precipitacao_anual(lat, lon, ano)
        if df_chuva.empty:
            print("\nNão foi possível gerar gráfico: dados vazios.")
            return

        # Agrega por mês
        df_mensal = agregar_por_meses(df_chuva)
        if df_mensal.empty:
            print("\nNão foi possível agregar dados mensais.")
            return

        try:
            # Conecta ao banco de dados
            conn = sqlite3.connect("analise_anual.db")
            
            # Cria tabela e salva dados
            criar_tabela_sqlite_anual(conn)
            salvar_dados_sqlite_anual(conn, cep, ano, lat, lon, df_mensal)
            
        except sqlite3.Error as e:
            print(f"\nErro no banco de dados: {str(e)}")
            
        finally:
            # Garante que a conexão será fechada
            if 'conn' in locals():
                conn.close()

        # Gera o gráfico
        plotar_grafico_mensal(df_mensal, ano, cep)

    # Trata interrupção pelo usuário (Ctrl+C)
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        
    # Trata outros erros inesperados
    except Exception as e:
        print(f"\nErro inesperado: {str(e)}")

# Ponto de entrada principal
if __name__ == "__main__":
    pricip_anual()