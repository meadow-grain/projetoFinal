Este é um projeto académico e de portfólio que simula um ambiente real de operações de receitas (RevOps) e análise de dados para uma empresa de leasing de camiões nos Estados Unidos, focada em atrair motoristas independentes (Owner-Operators).

O projeto é composto por duas partes principais:

1. Robô de Geração de Dados (ETL / Faker): Um script que simula a entrada de leads (potenciais clientes) em tempo real, aplicando regras de negócio complexas, vieses geográficos e comportamentais.
2. Dashboard Interativo (Streamlit): Um painel de inteligência em tempo real para analisar o funil de vendas, perfil de cliente ideal (ICP), viabilidade financeira e eficiência operacional, integrado com Inteligência Artificial para recomendações estratégicas.

✨ Funcionalidades Principais:

1. Simulação de Dados Realista: Geração de leads utilizando a biblioteca Faker, com lógicas complexas que cruzam a experiência do motorista (Anos de CDL), o custo de vida do estado (ex: Northeast vs Midwest) e a sua motivação principal para determinar as suas expectativas financeiras e a rota desejada (OTR, Regional ou Local).
2. Painel em Tempo Real: O dashboard atualiza-se automaticamente a cada 15 segundos para refletir as captações mais recentes do sistema.
3. Análise Geográfica: Mapas coropléticos e gráficos que cruzam a localização com o tipo de equipamento (Reefer, Dry Van, Flatbed) e rotas.
4. Métricas Financeiras (Gap de Realidade): Análise detalhada entre a expectativa de ganhos do motorista e a previsão matemática real do sistema (RPM, Milhas, Dias de Folga).
5. Consultor de IA Integrado: Integração com o modelo Google Gemini para ler as métricas filtradas no painel e gerar relatórios táticos de ação instantâneos para as equipas de Vendas (SDRs) e Marketing.

🛠️ Tecnologias Utilizadas
Linguagem: Python 3.9+
Interface de Dados / Web: Streamlit, Streamlit-Autorefresh
Visualização de Dados: Plotly Express
Base de Dados: MySQL (via SQLAlchemy e PyMySQL)
Geração de Dados Sintéticos: Faker, Schedule
Inteligência Artificial: API do Google GenAI (Gemini 1.5 Flash)

⚙️ Pré-requisitos e Configuração
1. Base de Dados
Precisas de ter o MySQL Server instalado e a correr localmente (ou alterar a connection string para um servidor remoto).
Cria a base de dados que irá receber os dados:

SQL
CREATE DATABASE leasing_prospects;

2. Dependências Python
Instala as bibliotecas necessárias. Podes criar um ficheiro requirements.txt com o seguinte:

streamlit
pandas
sqlalchemy
pymysql
streamlit-autorefresh
plotly
faker
schedule
google-genai

Instale-as executando:

Bash
pip install -r requirements.txt
3. Variáveis de Ambiente (API Key do Gemini)
Para que o módulo de Consultoria IA funcione, deves configurar a chave da API do Google Gemini.
Na raiz do teu projeto, cria uma pasta .streamlit e dentro dela um ficheiro secrets.toml:

Ini, TOML
# .streamlit/secrets.toml
GEMINI_API_KEY = "COLA_A_TUA_CHAVE_AQUI"

🚀 Como Executar o Projeto
O ecossistema funciona melhor quando executas os dois scripts em terminais separados.

Passo 1: Iniciar o Robô Gerador de Leads
Abre um terminal e executa o scheduler. Ele irá injetar entre 10 a 20 leads no banco de dados a cada 30 segundos.

Bash
python scheduler.py
Passo 2: Iniciar o Dashboard
Abre um segundo terminal e inicia a aplicação Streamlit.

Bash
streamlit run dashboard.py
O painel abrirá automaticamente no teu navegador padrão (normalmente em http://localhost:8501).

🧠 Regras de Negócio Implementadas (O "Motor" do Faker)
Para tornar os dados o mais próximos possível da realidade, o script gerador não atira dados aleatórios. Ele segue vieses lógicos:

- Fator de Experiência (CDL): Condutores veteranos tendem a preferir rotas Regionais ou Locais, enquanto condutores com pouca experiência são empurrados para as rotas interestaduais (OTR).

- Fator Geográfico: Fortes concentrações logísticas (Texas e Califórnia) recebem bónus de volume. Motoristas do Northeast exigem expectativas salariais maiores devido ao custo de vida, enquanto os do Midwest aceitam valores menores.

- Fator Motivacional: Motoristas cuja principal dor é a "Falta de Tempo em Casa" fogem do OTR e exigem mais dias de folga, reduzindo os seus ganhos e a taxa de qualificação financeira.

- Desqualificação Direta: Condutores localizados no Alasca (AK) ou Havai (HI) ou sem anos de experiência comercial (0 anos) são desqualificados matematicamente pelo algoritmo.

👨‍💻 Autor
Desenvolvido como projeto de conclusão/portefólio em Ciência de Dados e Inteligência Comercial.

Nome: Victor Gabriel Santos da Fé

LinkedIn: https://www.linkedin.com/in/victor-da-fe/

Email: victordafe49@gmail.com
