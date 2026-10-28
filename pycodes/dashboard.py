import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from streamlit_autorefresh import st_autorefresh
import plotly.express as px
from google import genai
import datetime

st_autorefresh(interval=5000, limit=None, key="atualizacao_leads")

st.set_page_config(page_title="Dashboard - Leasing", page_icon="📊", layout="wide")

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.title("📊 Painel de Inteligência Comercial (Live)")

STRING_CONEXAO = st.secrets["DB_URI"]
engine = create_engine(STRING_CONEXAO, connect_args={"ssl": {"ssl_mode": "REQUIRED"}})

try:
    with engine.connect() as conexao:
        df_meta = pd.read_sql("SELECT MIN(DATE(criado_em)) as min_date, MAX(DATE(criado_em)) as max_date, MAX(anos_cdl) as max_cdl FROM leads", conexao)
        df_filtros_db = pd.read_sql("SELECT DISTINCT estado, rota, trailer FROM leads", conexao)
except Exception as e:
    st.error(f"Erro ao ligar à base de dados: {e}")
    st.stop()

if pd.isnull(df_meta['min_date'][0]):
    st.warning("Nenhum dado encontrado na base de dados. Ligue o robô gerador primeiro.")
    st.stop()

min_date = df_meta['min_date'][0]
max_date = df_meta['max_date'][0]
max_cdl = int(df_meta['max_cdl'][0]) if pd.notnull(df_meta['max_cdl'][0]) else 40

estados_com_dados = df_filtros_db['estado'].dropna().unique().tolist()
rotas_com_dados = sorted(df_filtros_db['rota'].dropna().unique().tolist())
trailers_com_dados = sorted(df_filtros_db['trailer'].dropna().unique().tolist())

MAPEAMENTO_REGIOES = {
    "CA": "West", "OR": "West", "WA": "West", "AK": "West", "HI": "West", "NV": "West", "ID": "West", "UT": "West", "MT": "West", "WY": "West", "CO": "West",
    "AZ": "Southwest", "NM": "Southwest", "TX": "Southwest", "OK": "Southwest",
    "IL": "Midwest", "IN": "Midwest", "MI": "Midwest", "OH": "Midwest", "WI": "Midwest", "IA": "Midwest", "KS": "Midwest", "MN": "Midwest", "MO": "Midwest", "NE": "Midwest", "ND": "Midwest", "SD": "Midwest",
    "CT": "Northeast", "ME": "Northeast", "MA": "Northeast", "NH": "Northeast", "NJ": "Northeast", "NY": "Northeast", "PA": "Northeast", "RI": "Northeast", "VT": "Northeast", "DE": "Northeast", "MD": "Northeast",
    "AL": "Southeast", "FL": "Southeast", "GA": "Southeast", "KY": "Southeast", "MS": "Southeast", "NC": "Southeast", "SC": "Southeast", "TN": "Southeast", "VA": "Southeast", "WV": "Southeast", "AR": "Southeast", "LA": "Southeast"
}

df_regioes_temp = pd.DataFrame({'estado': estados_com_dados})
df_regioes_temp['regiao'] = df_regioes_temp['estado'].map(MAPEAMENTO_REGIOES).fillna('Outro')
regioes_unicas = sorted(df_regioes_temp['regiao'].unique())

LABELS_DICT = {
    'contagem': 'Volume de Leads',
    'faixa_experiencia': 'Tempo de CDL',
    'rota': 'Rota',
    'trailer': 'Equipamento',
    'regiao': 'Região',
    'estado': 'Estado',
    'dor_cliente': 'Motivação/Dor',
    'expectativa_ganho': 'Expectativa de Ganho ($)',
    'previsao_ganho': 'Previsão de Ganho ($)',
    'milhas': 'Milhas Rodadas',
    'folgas': 'Dias de Folga (Mês)',
    'rpm': 'Rate Per Mile ($/mi)',
    'data_criacao': 'Data',
    'leads': 'Volume de Leads',
    'valores': 'Quantidade',
    'etapa': 'Fase do Funil',
    'grupo_expectativa': 'Faixa de Expectativa ($)',
    'status_emprego': 'Situação Atual',
    'taxa_qual': 'Taxa de Qualificação (%)'
}

def reset_filtros():
    st.session_state.filtro_data = (min_date, max_date)
    st.session_state.filtro_regiao = regioes_unicas
    st.session_state.filtro_estado = sorted(estados_com_dados)
    st.session_state.filtro_rota = rotas_com_dados
    st.session_state.filtro_trailer = trailers_com_dados
    st.session_state.filtro_cdl = (0, max_cdl)
    st.session_state.filtro_qual = "Todos"

if "filtro_estado" not in st.session_state:
    st.session_state.filtro_estado = sorted(estados_com_dados)
if "filtro_regiao" not in st.session_state:
    st.session_state.filtro_regiao = regioes_unicas

def atualiza_estados_por_regiao():
    regioes_selecionadas = st.session_state.filtro_regiao
    if regioes_selecionadas:
        estados_correspondentes = sorted(df_regioes_temp[df_regioes_temp['regiao'].isin(regioes_selecionadas)]['estado'].tolist())
    else:
        estados_correspondentes = sorted(estados_com_dados)
    st.session_state.filtro_estado = estados_correspondentes

st.sidebar.header("🎛️ Filtros Globais")

datas_selecionadas = st.sidebar.date_input("Período de Captação", [min_date, max_date], min_value=min_date, max_value=max_date, format="DD/MM/YYYY", key="filtro_data")

if len(datas_selecionadas) == 2:
    data_inicio, data_fim = datas_selecionadas
else:
    data_inicio = data_fim = datas_selecionadas[0]

dias_selecionados = (data_fim - data_inicio).days + 1
data_inicio_prev = data_inicio - datetime.timedelta(days=dias_selecionados)

regioes_selecionadas = st.sidebar.multiselect(
    "Filtrar por Região", 
    regioes_unicas, 
    key="filtro_regiao",
    on_change=atualiza_estados_por_regiao
)

if regioes_selecionadas:
    estados_disponiveis = sorted(df_regioes_temp[df_regioes_temp['regiao'].isin(regioes_selecionadas)]['estado'].tolist())
else:
    estados_disponiveis = sorted(estados_com_dados)
    
estados_selecionados = st.sidebar.multiselect(
    "Filtrar por Estado", 
    estados_disponiveis, 
    key="filtro_estado"
)

rotas_selecionadas = st.sidebar.multiselect("Filtrar por Rota", rotas_com_dados, default=rotas_com_dados, key="filtro_rota")
trailers_selecionados = st.sidebar.multiselect("Filtrar por Equipamento", trailers_com_dados, default=trailers_com_dados, key="filtro_trailer")
faixa_cdl_selecionada = st.sidebar.slider("Anos de CDL", 0, max_cdl, (0, max_cdl), key="filtro_cdl")
filtro_qualificacao = st.sidebar.radio("Status de Qualificação", ["Todos", "Apenas Qualificados", "Apenas Desqualificados"], key="filtro_qual")

st.sidebar.markdown("---")
st.sidebar.button("🔄 Resetar Filtros", use_container_width=True, on_click=reset_filtros)

if not estados_selecionados or not rotas_selecionadas or not trailers_selecionados:
    df_geral = pd.DataFrame()
else:
    query = "SELECT * FROM leads WHERE DATE(criado_em) BETWEEN %s AND %s"
    params = [data_inicio_prev, data_fim]
    
    placeholders_est = ', '.join(['%s'] * len(estados_selecionados))
    query += f" AND estado IN ({placeholders_est})"
    params.extend(estados_selecionados)
    
    placeholders_rota = ', '.join(['%s'] * len(rotas_selecionadas))
    query += f" AND rota IN ({placeholders_rota})"
    params.extend(rotas_selecionadas)
    
    placeholders_trailer = ', '.join(['%s'] * len(trailers_selecionados))
    query += f" AND trailer IN ({placeholders_trailer})"
    params.extend(trailers_selecionados)
    
    query += " AND anos_cdl BETWEEN %s AND %s"
    params.extend([faixa_cdl_selecionada[0], faixa_cdl_selecionada[1]])
    
    if filtro_qualificacao == "Apenas Qualificados":
        query += " AND qualificou = 1"
    elif filtro_qualificacao == "Apenas Desqualificados":
        query += " AND qualificou = 0"

    try:
        with engine.connect() as conexao:
            df_geral = pd.read_sql(query, conexao, params=tuple(params))
    except Exception as e:
        st.error(f"Erro ao executar a consulta otimizada: {e}")
        df_geral = pd.DataFrame()

if not df_geral.empty:
    df_geral['criado_em'] = pd.to_datetime(df_geral['criado_em'])
    df_geral['data_criacao'] = df_geral['criado_em'].dt.date
    
    if 'previsao_ganho' not in df_geral.columns:
        def calc_previsao(row):
            mult_trailer = 0.83 if row['trailer'] == "Dry Van" else (1.30 if row['trailer'] == "Flatbed" else 1.10)
            mult_rota = 1.20 if row['rota'] == 'OTR' else (0.90 if row['rota'] == 'Regional' else 0.65)
            return (row['milhas'] * mult_trailer * mult_rota) * (1 - (row['folgas'] * 0.05))
        df_geral['previsao_ganho'] = df_geral.apply(calc_previsao, axis=1)

    faixas_cdl = [-1, 5, 10, 15, 20, 25, 100]
    labels_cdl = ['0-5 anos', '6-10 anos', '11-15 anos', '16-20 anos', '21-25 anos', '26+ anos']
    df_geral['faixa_experiencia'] = pd.cut(df_geral['anos_cdl'], bins=faixas_cdl, labels=labels_cdl)
    
    df_geral['status_emprego'] = df_geral['empregado'].map({1: 'Empregado', 0: 'Desempregado', True: 'Empregado', False: 'Desempregado'})
    df_geral['regiao'] = df_geral['estado'].map(MAPEAMENTO_REGIOES).fillna('Outro')

    df_prev = df_geral[(df_geral['data_criacao'] >= data_inicio_prev) & (df_geral['data_criacao'] < data_inicio)]
    df_filtrado = df_geral[(df_geral['data_criacao'] >= data_inicio) & (df_geral['data_criacao'] <= data_fim)]

    if df_filtrado.empty:
        st.warning("Nenhum dado corresponde aos filtros no período atual selecionado.")
    else:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Visão Executiva", 
            "Inteligência Geográfica", 
            "Raio-X do ICP", 
            "Gap Financeiro", 
            "Desempenho Operacional",
            "✨ Plano de Ação (IA)"
        ])
        
        with tab1:
            total_leads = len(df_filtrado)
            leads_qualificados = len(df_filtrado[df_filtrado['qualificou'] == 1])
            taxa_qualificacao = (leads_qualificados / total_leads) * 100 if total_leads > 0 else 0
            media_expectativa = df_filtrado['expectativa_ganho'].mean()

            total_leads_prev = len(df_prev)
            leads_qual_prev = len(df_prev[df_prev['qualificou'] == 1])
            taxa_qual_prev = (leads_qual_prev / total_leads_prev) * 100 if total_leads_prev > 0 else 0
            media_exp_prev = df_prev['expectativa_ganho'].mean() if total_leads_prev > 0 else 0

            delta_total = total_leads - total_leads_prev
            delta_qual = leads_qualificados - leads_qual_prev
            delta_taxa = taxa_qualificacao - taxa_qual_prev
            delta_exp = media_expectativa - media_exp_prev
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Total de Leads", value=total_leads, delta=int(delta_total))
            with col2:
                st.metric(label="Leads Qualificados", value=leads_qualificados, delta=int(delta_qual))
            with col3:
                st.metric(label="Taxa de Qualificação", value=f"{taxa_qualificacao:.1f}%", delta=f"{delta_taxa:.1f}%")
            with col4:
                st.metric(label="Expectativa Média", value=f"${media_expectativa:,.2f}", delta=f"${delta_exp:,.2f}")
            
            st.markdown("---")
            
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                df_evolucao = df_filtrado.groupby('data_criacao').size().reset_index(name='leads')
                fig_evolucao = px.area(df_evolucao, x='data_criacao', y='leads', title="Evolução da Captação", markers=True, labels=LABELS_DICT)
                fig_evolucao.update_layout(xaxis_title="Data de Captação", yaxis_title="Volume de Leads")
                st.plotly_chart(fig_evolucao, use_container_width=True)
                
            with col_graf2:
                perfil_valido = len(df_filtrado[(df_filtrado['anos_cdl'] >= 1) & (df_filtrado['anos_cdl'] <= 30)])
                dados_funil = dict(
                    etapa=['Total Captado', 'Perfil Válido (1 a 30 Anos CDL)', 'Qualificados'],
                    valores=[total_leads, perfil_valido, leads_qualificados]
                )
                fig_funil = px.funnel(dados_funil, x='valores', y='etapa', title="Funil de Qualificação", color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c'], labels=LABELS_DICT)
                fig_funil.update_layout(yaxis_title="")
                st.plotly_chart(fig_funil, use_container_width=True)

            st.markdown("---")
            st.markdown("### Últimos Leads Captados")
            colunas_tabela = ['nome', 'regiao', 'estado', 'anos_cdl', 'trailer', 'rota', 'status_emprego', 'expectativa_ganho', 'previsao_ganho', 'qualificou']
            df_tabela = df_filtrado.sort_values(by='criado_em', ascending=False)[colunas_tabela].head(10).copy()
            df_tabela['qualificou'] = df_tabela['qualificou'].apply(lambda x: 'Sim' if x == 1 else 'Não')
            
            df_tabela = df_tabela.rename(columns={
                'nome': 'Nome', 'regiao': 'Região', 'estado': 'Estado',
                'anos_cdl': 'Anos de CDL', 'trailer': 'Equipamento', 'rota': 'Rota',
                'status_emprego': 'Situação Atual', 'expectativa_ganho': 'Expectativa ($)',
                'previsao_ganho': 'Previsão ($)', 'qualificou': 'Qualificou?'
            })
            st.dataframe(df_tabela, use_container_width=True)

        with tab2:
            col_geo1, col_geo2 = st.columns([6, 4])
            
            with col_geo1:
                df_mapa = df_filtrado.groupby('estado').agg(
                    total=('nome', 'count'),
                    qualificados=('qualificou', 'sum')
                ).reset_index()
                df_mapa['taxa_qual'] = (df_mapa['qualificados'] / df_mapa['total']) * 100
                
                fig_mapa = px.choropleth(
                    df_mapa, locations='estado', locationmode="USA-states", color='taxa_qual', scope="usa",
                    hover_data=['total', 'qualificados'],
                    title="Eficiência Geográfica: Taxa de Qualificação por Estado (%)", 
                    color_continuous_scale="Greens", labels=LABELS_DICT
                )
                fig_mapa.update_layout(margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_mapa, use_container_width=True)

            with col_geo2:
                df_qual_reg = df_filtrado.groupby(['regiao', 'qualificou']).size().reset_index(name='contagem')
                df_qual_reg['Status'] = df_qual_reg['qualificou'].apply(lambda x: 'Qualificado' if x else 'Reprovado')
                fig_qual_reg = px.bar(
                    df_qual_reg, x='regiao', y='contagem', color='Status', barmode='group',
                    title="Status por Região",
                    color_discrete_map={'Qualificado': '#2ca02c', 'Reprovado': '#d62728'}, labels=LABELS_DICT
                )
                fig_qual_reg.update_layout(xaxis_title="Região", yaxis_title="Volume de Leads")
                st.plotly_chart(fig_qual_reg, use_container_width=True)

            st.markdown("---")
            
            col_geo3, col_geo4 = st.columns(2)
            
            with col_geo3:
                df_rota_regiao = df_filtrado.groupby(['regiao', 'rota']).size().reset_index(name='contagem')
                fig_rota_regiao = px.bar(
                    df_rota_regiao, x='contagem', y='regiao', color='rota', orientation='h',
                    title="Preferência de Rota por Região",
                    color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c'], labels=LABELS_DICT
                )
                fig_rota_regiao.update_layout(barmode='stack', yaxis={'categoryorder':'total ascending'}, xaxis_title="Volume de Leads", yaxis_title="Região")
                st.plotly_chart(fig_rota_regiao, use_container_width=True)
                
            with col_geo4:
                df_trailer_geo = df_filtrado.groupby(['regiao', 'estado', 'trailer']).size().reset_index(name='contagem')
                fig_treemap = px.treemap(
                    df_trailer_geo, path=['regiao', 'estado', 'trailer'], values='contagem',
                    title="Proporção de Equipamentos por Região e Estado", color='trailer', labels=LABELS_DICT
                )
                fig_treemap.update_layout(margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_treemap, use_container_width=True)

        with tab3:
            col_icp1, col_icp2 = st.columns(2)
            
            with col_icp1:
                df_icp = df_filtrado.groupby(['faixa_experiencia', 'rota'], observed=False).size().reset_index(name='contagem')
                fig_icp = px.bar(
                    df_icp, x='faixa_experiencia', y='contagem', color='rota',
                    title="Migração de Perfil: Rota por Tempo de CDL",
                    color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c'], labels=LABELS_DICT
                )
                fig_icp.update_layout(
                    barmode='stack', barnorm='percent', xaxis_title="Anos de CDL", yaxis_title="Proporção (%)",
                    xaxis={'categoryorder':'array', 'categoryarray':labels_cdl}
                )
                st.plotly_chart(fig_icp, use_container_width=True)
                
            with col_icp2:
                df_trailer_cdl = df_filtrado.groupby(['faixa_experiencia', 'trailer'], observed=False).size().reset_index(name='contagem')
                fig_trailer_cdl = px.bar(
                    df_trailer_cdl, x='faixa_experiencia', y='contagem', color='trailer', barmode='group',
                    title="Preferência de Equipamento por Maturidade (CDL)", labels=LABELS_DICT
                )
                fig_trailer_cdl.update_layout(
                    xaxis_title="Anos de CDL", yaxis_title="Volume de Leads",
                    xaxis={'categoryorder':'array', 'categoryarray':labels_cdl}
                )
                st.plotly_chart(fig_trailer_cdl, use_container_width=True)
                
            st.markdown("---")
            
            col_icp3, col_icp4 = st.columns(2)
            
            with col_icp3:
                df_dores = df_filtrado['dor_cliente'].value_counts().reset_index()
                df_dores.columns = ['dor_cliente', 'contagem']
                fig_dores = px.pie(
                    df_dores, names='dor_cliente', values='contagem', hole=0.4,
                    title="Matriz de Dores e Motivações Principais", labels=LABELS_DICT
                )
                st.plotly_chart(fig_dores, use_container_width=True)
                
            with col_icp4:
                df_dores_rota = df_filtrado.groupby(['dor_cliente', 'rota']).size().reset_index(name='contagem')
                fig_dores_rota = px.bar(
                    df_dores_rota, x='contagem', y='dor_cliente', color='rota', orientation='h',
                    title="Origem das Objeções: Motivações vs. Rotas",
                    color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c'], labels=LABELS_DICT
                )
                fig_dores_rota.update_layout(barmode='stack', xaxis_title="Volume de Leads", yaxis_title="Motivação/Dor", yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_dores_rota, use_container_width=True)
                
            st.markdown("---")
            
            col_icp5, col_icp6 = st.columns(2)
            
            with col_icp5:
                df_qual_trailer = df_filtrado.groupby(['trailer', 'qualificou']).size().reset_index(name='contagem')
                df_qual_trailer['Status'] = df_qual_trailer['qualificou'].apply(lambda x: 'Qualificado' if x else 'Reprovado')
                fig_qual_trailer = px.bar(
                    df_qual_trailer, x='trailer', y='contagem', color='Status', barmode='group',
                    title="Taxa de Qualificação por Equipamento",
                    color_discrete_map={'Qualificado': '#2ca02c', 'Reprovado': '#d62728'}, labels=LABELS_DICT
                )
                fig_qual_trailer.update_layout(xaxis_title="Equipamento", yaxis_title="Volume de Leads")
                st.plotly_chart(fig_qual_trailer, use_container_width=True)
                
            with col_icp6:
                df_qual_emp = df_filtrado.groupby(['status_emprego', 'qualificou']).size().reset_index(name='contagem')
                df_qual_emp['Status'] = df_qual_emp['qualificou'].apply(lambda x: 'Qualificado' if x else 'Reprovado')
                fig_qual_emp = px.bar(
                    df_qual_emp, x='status_emprego', y='contagem', color='Status', barmode='group',
                    title="Taxa de Qualificação por Situação Atual",
                    color_discrete_map={'Qualificado': '#2ca02c', 'Reprovado': '#d62728'}, labels=LABELS_DICT
                )
                fig_qual_emp.update_layout(xaxis_title="Situação Atual", yaxis_title="Volume de Leads")
                st.plotly_chart(fig_qual_emp, use_container_width=True)

        with tab4:
            col_fin1, col_fin2 = st.columns(2)
            
            with col_fin1:
                faixas_exp = [0, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 10000]
                labels_exp = ['< $1000', '$1000-$1500', '$1500-$2000', '$2000-$2500', '$2500-$3000', '$3000-$3500', '$3500-$4000', '> $4000']
                df_filtrado['grupo_expectativa'] = pd.cut(df_filtrado['expectativa_ganho'], bins=faixas_exp, labels=labels_exp)
                df_exp = df_filtrado.groupby('grupo_expectativa', observed=False).size().reset_index(name='contagem')
                fig_exp = px.bar(df_exp, x='grupo_expectativa', y='contagem', title="Distribuição de Expectativa de Ganhos", color_discrete_sequence=['#9467bd'], labels=LABELS_DICT)
                fig_exp.update_layout(xaxis_title="Faixa de Expectativa ($)", yaxis_title="Volume de Leads")
                st.plotly_chart(fig_exp, use_container_width=True)
                
            with col_fin2:
                df_regiao_exp = df_filtrado.groupby('regiao')['expectativa_ganho'].mean().reset_index().sort_values('expectativa_ganho', ascending=False)
                fig_regiao_exp = px.bar(
                    df_regiao_exp, x='regiao', y='expectativa_ganho',
                    title="Média de Expectativa por Região",
                    color='expectativa_ganho', color_continuous_scale='Viridis', labels=LABELS_DICT
                )
                fig_regiao_exp.update_layout(xaxis_title="Região", yaxis_title="Expectativa Média ($)")
                st.plotly_chart(fig_regiao_exp, use_container_width=True)
                
            st.markdown("---")
            
            df_filtrado['Status'] = df_filtrado['qualificou'].apply(lambda x: 'Qualificado' if x else 'Reprovado')
            fig_scatter = px.scatter(
                df_filtrado, x='expectativa_ganho', y='previsao_ganho', color='Status', opacity=0.7,
                title="Corte de Realidade: Previsão vs Expectativa",
                color_discrete_map={'Qualificado': '#2ca02c', 'Reprovado': '#d62728'},
                hover_data=['nome', 'regiao', 'estado'], labels=LABELS_DICT
            )
            max_val = max(df_filtrado['expectativa_ganho'].max(), df_filtrado['previsao_ganho'].max())
            fig_scatter.add_shape(type='line', x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color='white', dash='dash'))
            fig_scatter.update_layout(xaxis_title="Expectativa de Ganho ($)", yaxis_title="Previsão do Sistema ($)")
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            st.markdown("---")
            
            col_fin4, col_fin5 = st.columns(2)
            
            with col_fin4:
                fig_box = px.box(
                    df_filtrado, x='faixa_experiencia', y='expectativa_ganho', color='faixa_experiencia',
                    title="Dispersão de Expectativa de Ganhos por CDL", labels=LABELS_DICT
                )
                fig_box.update_layout(
                    showlegend=False, xaxis_title="Anos de CDL", yaxis_title="Expectativa ($)",
                    xaxis={'categoryorder':'array', 'categoryarray':labels_cdl}
                )
                st.plotly_chart(fig_box, use_container_width=True)
                
            with col_fin5:
                fig_exp_emp = px.box(
                    df_filtrado, x='status_emprego', y='expectativa_ganho', color='status_emprego',
                    title="Expectativa de Ganhos: Empregados vs Desempregados",
                    color_discrete_sequence=['#17becf', '#bcbd22'], labels=LABELS_DICT
                )
                fig_exp_emp.update_layout(showlegend=False, xaxis_title="Situação Atual", yaxis_title="Expectativa ($)")
                st.plotly_chart(fig_exp_emp, use_container_width=True)

        with tab5:
            col_op1, col_op2 = st.columns(2)
            
            with col_op1:
                df_esforco = df_filtrado.groupby(['folgas', 'rota'], as_index=False)['previsao_ganho'].mean()
                fig_esforco = px.bar(
                    df_esforco, x='folgas', y='previsao_ganho', color='rota', barmode='group',
                    title="Média de Ganhos vs. Dias de Folga",
                    color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c'], labels=LABELS_DICT
                )
                fig_esforco.update_layout(
                    xaxis_title="Dias de Folga (Mês)", 
                    yaxis_title="Previsão Média de Ganhos ($)",
                    xaxis=dict(dtick=1)
                )
                st.plotly_chart(fig_esforco, use_container_width=True)
                
            with col_op2:
                df_filtrado['rpm'] = df_filtrado['previsao_ganho'] / df_filtrado['milhas']
                fig_rpm = px.box(
                    df_filtrado, x='trailer', y='rpm', color='trailer',
                    title="Eficiência Financeira: Rate Per Mile (RPM) por Equipamento", labels=LABELS_DICT
                )
                fig_rpm.update_layout(showlegend=False, xaxis_title="Equipamento", yaxis_title="Rate Per Mile ($/mi)")
                st.plotly_chart(fig_rpm, use_container_width=True)

            st.markdown("---")

            col_op3, col_op4 = st.columns(2)

            with col_op3:
                df_milhas_cdl = df_filtrado.groupby('faixa_experiencia', observed=False)['milhas'].mean().reset_index()
                df_milhas_cdl['faixa_experiencia'] = df_milhas_cdl['faixa_experiencia'].astype(str)
                
                fig_line_cdl = px.line(
                    df_milhas_cdl, x='faixa_experiencia', y='milhas', markers=True,
                    title="Milhagem Média por Experiência (CDL)", labels=LABELS_DICT
                )
                fig_line_cdl.update_layout(
                    xaxis_title="Anos de CDL", yaxis_title="Média de Milhas",
                    xaxis={'categoryorder':'array', 'categoryarray':labels_cdl}
                )
                fig_line_cdl.update_traces(line_color='#e377c2', marker=dict(size=10))
                st.plotly_chart(fig_line_cdl, use_container_width=True)
                
            with col_op4:
                fig_folgas_rota = px.box(
                    df_filtrado, x='rota', y='folgas', color='rota',
                    title="Distribuição de Dias de Folga por Rota",
                    color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c'], labels=LABELS_DICT
                )
                fig_folgas_rota.update_layout(showlegend=False, xaxis_title="Rota", yaxis_title="Dias de Folga (Mês)")
                st.plotly_chart(fig_folgas_rota, use_container_width=True)

        with tab6:
            st.markdown("### Consultoria Estratégica com Gemini AI")
            st.write("Gere um relatório executivo com recomendações de abordagem e ajustes de campanha baseados nos dados atuais filtrados no painel.")
            
            if "relatorio_ia" not in st.session_state:
                st.session_state.relatorio_ia = None

            if st.button("🧠 Gerar Plano de Ação para a Diretoria", type="primary"):
                with st.spinner("Analisando dados da base e gerando insights operacionais..."):
                    try:
                        total_leads_ia = len(df_filtrado)
                        taxa_qual_ia = (len(df_filtrado[df_filtrado['qualificou'] == 1]) / total_leads_ia) * 100 if total_leads_ia > 0 else 0
                        top_estado = df_filtrado['estado'].mode()[0] if not df_filtrado.empty else "N/A"
                        top_dor = df_filtrado['dor_cliente'].mode()[0] if not df_filtrado.empty else "N/A"
                        gap_financeiro = df_filtrado['expectativa_ganho'].mean() - df_filtrado['previsao_ganho'].mean()
                        rota_dominante = df_filtrado['rota'].mode()[0] if not df_filtrado.empty else "N/A"
                        
                        prompt_estrategico = f"""
                        Você é um Diretor de Inteligência Comercial (RevOps) em uma empresa que faz leasing de caminhões para motoristas nos EUA (Owner-Operators).
                        Analise os seguintes dados em tempo real da nossa captação de leads e crie um plano de ação tático com 3 tópicos diretos e acionáveis para o time de SDRs e Marketing.
                        
                        Métricas atuais do funil (Base de {total_leads_ia} leads):
                        - Taxa de Qualificação Geral: {taxa_qual_ia:.1f}%
                        - Região/Estado de Maior Volume: {top_estado}
                        - Rota Preferida: {rota_dominante}
                        - Principal Objeção/Dor dos Motoristas: {top_dor}
                        - Gap Financeiro Médio (Expectativa do Lead vs Nossa Previsão): ${gap_financeiro:.2f}
                        
                        Estruture sua resposta em Markdown com:
                        1. Diagnóstico Rápido (O que esses números significam).
                        2. Ajuste de Discurso para SDRs (Como contornar a principal dor considerando o Gap Financeiro).
                        3. Direcionamento de Marketing (Onde focar as próximas campanhas geográficas e de equipamento).
                        
                        Seja direto, focado em vendas B2B e use jargões de logística norte-americana quando fizer sentido.
                        """
                        
                        interaction = client.interactions.create(
                            model="gemini-3.8-flash",
                            input=prompt_estrategico
                        )
                        
                        st.session_state.relatorio_ia = interaction.output_text
                        st.success("Análise concluída com sucesso!")
                        
                    except Exception as e:
                        st.error(f"Erro ao comunicar com a API do Gemini: {e}. Verifique sua API Key e conexão.")
            
            if st.session_state.relatorio_ia:
                st.markdown("---")
                st.markdown(st.session_state.relatorio_ia)
else:
    st.warning("Nenhum dado encontrado na base de dados para construir o painel.")
