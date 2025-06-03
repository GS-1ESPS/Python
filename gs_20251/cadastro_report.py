#Importação das bibliotecas necessárias
import requests  #Para fazer requisições HTTP à API ViaCEP
import sqlite3   #Para trabalhar com banco de dados SQLite
from datetime import datetime  #Para manipular datas e horas

#Conexão com o banco de dados de usuários (cria se não existir)
conexao_usuarios = sqlite3.connect('usuarios.db')
#Cria um cursor para executar operações no banco de dados de usuários
operador_usuarios = conexao_usuarios.cursor()

#Conexão com o banco de dados de alagamentos (cria se não existir)
conexao_alagamentos = sqlite3.connect('alagamentos.db')
#Cria um cursor para executar operações no banco de dados de alagamentos
operador_alagamentos = conexao_alagamentos.cursor()

#Cria a tabela de usuários se ela não existir
operador_usuarios.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    nome_completo TEXT,                   
    cpf TEXT UNIQUE,                      
    tipo_deficiencia TEXT,                
    cep TEXT,                             
    endereco_completo TEXT,              
    necessita_resgate TEXT                
)
''')

#Cria a tabela de relatórios de alagamento se não existir
operador_alagamentos.execute('''
CREATE TABLE IF NOT EXISTS relatorios_alagamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    nome_reportante TEXT,                 
    cpf_reportante TEXT,                  
    cep_local TEXT,                       
    endereco_alagado TEXT,                
    intensidade_chuva TEXT,               
    nivel_inundacao TEXT,                 
    data_hora_registro TEXT               
)
''')

#Confirma as alterações nos bancos de dados
conexao_usuarios.commit()
conexao_alagamentos.commit()

#Função para validar se um CPF tem 11 dígitos numéricos
def validar_cpf(numero_cpf):
    return len(numero_cpf) == 11 and numero_cpf.isdigit()  # Retorna True se válido

#Função para consultar endereço via API ViaCEP
def consultar_endereco(cep):
    try:
        #Faz requisição GET para a API ViaCEP
        resposta_api = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
        #Converte a resposta JSON em um dicionário Python
        dados_cep = resposta_api.json()
        
        #Verifica se a API retornou erro
        if "erro" in dados_cep:
            print("CEP não encontrado.")
            return None
        
        #Formata o endereço completo a partir dos dados
        return f"{dados_cep['logradouro']}, {dados_cep['bairro']}, {dados_cep['localidade']} - {dados_cep['uf']}"
    except Exception as erro:
        print("Erro ao buscar endereço:", erro)
        return None

#Função para registrar um novo usuário
def registrar_usuario():
    try:
        #Solicita e armazena o nome completo
        nome_completo = input("Digite o nome completo: ").strip()

        #Solicita CPF e valida repetidamente até ser válido
        cpf = input("Digite o CPF (somente números): ").strip()
        while not validar_cpf(cpf):
            print("CPF inválido. Tente novamente.")
            cpf = input("Digite o CPF (somente números): ").strip()

        #Pergunta sobre deficiência e valida resposta
        resposta_deficiencia = input("Você possui alguma deficiência? (sim/não): ").strip().lower()
        while resposta_deficiencia not in ['sim', 'não', 'nao']:
            resposta_deficiencia = input("Responda com 'sim' ou 'não': ").strip().lower()

        #Se tiver deficiência, pergunta detalhes
        if resposta_deficiencia == 'sim':
            tipo_deficiencia = input("Qual o tipo de deficiência? ").strip()
            necessita_resgate = input("Precisa de suporte da Defesa Civil? (sim/não): ").strip().lower()
            while necessita_resgate not in ['sim', 'não', 'nao']:
                necessita_resgate = input("Responda com 'sim' ou 'não': ").strip().lower()
        else:
            tipo_deficiencia = "Nenhuma"
            necessita_resgate = "não"

        #Solicita CEP e valida até encontrar endereço
        cep = input("Digite o CEP (somente números): ").strip()
        endereco_completo = consultar_endereco(cep)
        while not endereco_completo:
            cep = input("CEP inválido. Digite novamente: ").strip()
            endereco_completo = consultar_endereco(cep)

        #Insere os dados na tabela de usuários
        operador_usuarios.execute('''
            INSERT OR IGNORE INTO usuarios (nome_completo, cpf, tipo_deficiencia, cep, endereco_completo, necessita_resgate)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nome_completo, cpf, tipo_deficiencia, cep, endereco_completo, necessita_resgate))
        
        #Confirma a inserção no banco de dados
        conexao_usuarios.commit()

        print("\nUsuário cadastrado com sucesso!\n")
    except Exception as erro:
        print("Erro no cadastro:", erro)

#Função para registrar um novo alagamento
def registrar_alagamento():
    try:
        #Solicita dados do reportante
        nome_reportante = input("Digite seu nome completo: ").strip()

        #Valida CPF do reportante
        cpf_reportante = input("Digite seu CPF (somente números): ").strip()
        while not validar_cpf(cpf_reportante):
            print("CPF inválido. Tente novamente.")
            cpf_reportante = input("Digite seu CPF (somente números): ").strip()

        #Valida CEP do local
        cep_local = input("Digite o CEP da área alagada (somente números): ").strip()
        endereco_alagado = consultar_endereco(cep_local)
        while not endereco_alagado:
            cep_local = input("CEP inválido. Digite novamente: ").strip()
            endereco_alagado = consultar_endereco(cep_local)

        #Opções válidas para intensidade da chuva
        opcoes_chuva = ['fraca', 'media', 'média', 'forte']
        intensidade_chuva = input("Nível da chuva (fraca, média, forte): ").strip().lower()
        while intensidade_chuva not in opcoes_chuva:
            intensidade_chuva = input("Informe um nível válido: fraca, média ou forte: ").strip().lower()

        #Opções válidas para nível de inundação
        opcoes_inundacao = ['alto', 'medio', 'médio', 'baixo']
        nivel_inundacao = input("Nível da água (alto, médio, baixo): ").strip().lower()
        while nivel_inundacao not in opcoes_inundacao:
            nivel_inundacao = input("Informe um nível válido: alto, médio ou baixo: ").strip().lower()

        #Obtém data e hora atuais formatadas
        data_hora_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        #Insere o relatório no banco de dados
        operador_alagamentos.execute('''
            INSERT INTO relatorios_alagamento (nome_reportante, cpf_reportante, cep_local, 
            endereco_alagado, intensidade_chuva, nivel_inundacao, data_hora_registro)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nome_reportante, cpf_reportante, cep_local, endereco_alagado, 
              intensidade_chuva, nivel_inundacao, data_hora_registro))
        
        #Confirma a inserção
        conexao_alagamentos.commit()

        print("\nRelatório de alagamento enviado com sucesso!\n")
    except Exception as erro:
        print("Erro no relatório:", erro)

#Função para verificar relatórios por CEP
def verificar_relatorios_cep():
    try:
        #Solicita CEP para consulta
        cep_consulta = input("Digite o CEP para consulta (somente números): ").strip()
        #Valida se CEP tem 8 dígitos
        if not cep_consulta.isdigit() or len(cep_consulta) != 8:
            print("CEP inválido. Deve conter 8 números.")
            return

        #Obtém a data atual no formato YYYY-MM-DD
        data_atual = datetime.now().strftime("%Y-%m-%d")

        #Conta quantos relatórios existem para este CEP hoje
        operador_alagamentos.execute('''
            SELECT COUNT(*) FROM relatorios_alagamento
            WHERE cep_local = ? AND data_hora_registro LIKE ?
        ''', (cep_consulta, f"{data_atual}%"))

        #Obtém o resultado da contagem
        total_relatorios = operador_alagamentos.fetchone()[0]

        #Exibe alerta se houver muitos relatórios
        if total_relatorios >= 5:
            print("\n🚨 Alerta: Área com múltiplos relatos de alagamento hoje! Cuidado! 🚨\n")
        else:
            print("\nPoucos relatos nesta região hoje, mas mantenha atenção.\n")

    except Exception as erro:
        print("Erro na consulta:", erro)

#Loop principal do programa (menu interativo)
while True:
    print("\nMENU PRINCIPAL")
    print("1 - Cadastrar novo usuário")
    print("2 - Registrar ocorrência de alagamento")
    print("3 - Verificar relatórios por CEP")
    print("4 - Encerrar programa")

    #Captura a opção do usuário
    opcao = input("Escolha uma opção: ").strip()

    #Executa a função correspondente à opção escolhida
    if opcao == '1':
        registrar_usuario()
    elif opcao == '2':
        registrar_alagamento()
    elif opcao == '3':
        verificar_relatorios_cep()
    elif opcao == '4':
        print("Encerrando o sistema...")
        break  # Sai do loop e encerra o programa
    else:
        print("Opção inválida. Tente novamente.")

#Exibe todos os usuários cadastrados
print("\nUsuários cadastrados:")
operador_usuarios.execute('SELECT * FROM usuarios')
for usuario in operador_usuarios.fetchall():
    print(usuario)

#Exibe todos os relatórios de alagamento
print("\nRelatórios de alagamento:")
operador_alagamentos.execute('SELECT * FROM relatorios_alagamento')
for relatorio in operador_alagamentos.fetchall():
    print(relatorio)

#Fecha as conexões com os bancos de dados
conexao_usuarios.close()
conexao_alagamentos.close()
