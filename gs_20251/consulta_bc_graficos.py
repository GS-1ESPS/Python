#Para consultar que as infos do banco de dados estão sendo salvas corretamente
import sqlite3

def consultar_dados_graficodiario():
    conn = sqlite3.connect('analise_diaria.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM chuva_semana')
    resultados = cursor.fetchall()
    
    if resultados:
        print("\n Dados da análise diária, separados por semanas:")
        for linha in resultados:
            cep, data, chuva = linha
            print(f"CEP: {cep} | Data: {data} | Chuva (mm): {chuva}")
    else:
        print("Nenhum dado encontrado no banco de dados diário.")
    
    conn.close()

import sqlite3

def consultar_dados_graficomensal():
    conn = sqlite3.connect("analise_mensal.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM precipitacao_mensal")
    resultados = cursor.fetchall()

    if resultados:
        print("\nDados da análise mensal separados por semana:\n")
        for linha in resultados:
            id_, cep, ano, mes, semana, precipitacao_mm, lat, lon = linha
            print(f"ID: {id_:03d} | CEP: {cep} | Ano: {ano} | Mês: {mes:02d} | Semana: {semana} | "
                  f"Precipitação: {precipitacao_mm:.2f} mm | Latitude: {lat:.4f} | Longitude: {lon:.4f}")
    else:
        print("Nenhum dado encontrado no banco.")

    conn.close()


def consultar_dados_graficoanual():
    conn = sqlite3.connect('analise_anual.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM precipitacao_anual')
    resultados = cursor.fetchall()
    
    if resultados:
        print("\n Dados da análise anual (média mensal de precipitação):")
        for linha in resultados:
            id_, cep, ano, mes, precipitacao, lat, lon = linha
            print(f"ID: {id_} | CEP: {cep} | Ano: {ano} | Mês: {mes} | Precipitação (mm): {precipitacao:.2f} | Lat: {lat} | Lon: {lon}")
    else:
        print("Nenhum dado encontrado no banco de dados anual.")
    
    conn.close()

# Chamada das funções com título explicativo
consultar_dados_graficodiario()
consultar_dados_graficomensal()
consultar_dados_graficoanual()
