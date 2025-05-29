# ChuvaSegura - Sistema de Monitoramento e Prevenção de Enchentes

## Visão Geral
Sistema Python para monitoramento, previsão e resposta a enchentes no Brasil, integrando dados meteorológicos e engajamento social.

## Funcionalidades
- 📝 Cadastro de pessoas com deficiência em áreas de risco
- 🚨 Reporte em tempo real de alagamentos
- 📍 Consulta de CEP para alertas
- 🔮 Análise preditiva com dados de satélite
- 📊 Gráficos interativos de chuva (diário/mensal/anual)
- 🗃️ Banco de dados histórico

## Tecnologias
**Python 3** com:
- `requests` (APIs ViaCEP/Open-Meteo)
- `sqlite3` (banco de dados)
- `matplotlib` (gráficos)
- `pandas` (análise de dados)
- `geopy` (geolocalização)

## Estrutura do Projeto
ChuvaSegura/
├── cadastro_reporte/ # Sistema principal
│ ├── main.py
│ ├── usuarios.db
│ └── alagamentos.db
├── analise_chuva/ # Módulos de análise
│ ├── diario/
│ ├── mensal/
│ └── anual/
└── docs/ # Documentação

#Integrantes:
##-Gabrielly Candido (RM: 560916)
##-Luiza Ribeiro (RM: 560200)
1ESPS - 2025 | 
