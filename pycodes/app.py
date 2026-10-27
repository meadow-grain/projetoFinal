import streamlit as st
from sqlalchemy import create_engine, text

STRING_CONEXAO = "mysql+pymysql://root:Marry79513.@localhost:3306/leasing_prospects"
engine = create_engine(STRING_CONEXAO)

ESTADOS_VALIDOS = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

st.set_page_config(page_title="CRM - Leasing Prospects", page_icon="🚛")
st.title("🚛 Qualificação de drivers")

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

if "mensagem_sucesso" in st.session_state:
    st.success(st.session_state["mensagem_sucesso"])
    del st.session_state["mensagem_sucesso"]

st.write("Insira os dados da prospecção. Todos os campos são obrigatórios.")

col1, col2 = st.columns(2)

with col1:
    nome = st.text_input("Nome do Motorista *", key=f"nome_{st.session_state.form_key}").strip().title()
    estado = st.text_input("Estado (Sigla, ex: TX, FL) *", max_chars=2, key=f"estado_{st.session_state.form_key}").strip().upper()
    anos_cdl = st.number_input("Tempo de CDL (Anos) *", min_value=0, step=1, value=None, key=f"anos_{st.session_state.form_key}")
    trailer = st.selectbox("Tipo de Trailer *", ["Dry Van", "Flatbed", "Reefer"], index=None, key=f"trailer_{st.session_state.form_key}")
    rota = st.selectbox("Rota Desejada *", ["OTR", "Regional", "Local"], index=None, key=f"rota_{st.session_state.form_key}")
    dor_cliente = st.selectbox("Principal Dor / Motivação *", ["Mais dinheiro/milhas", "Equipamento", "Comunicação", "Mais folga", "Outros"], index=None, key=f"dor_{st.session_state.form_key}")

with col2:
    milhas = st.number_input("Milhagem Semanal Média *", min_value=0, step=100, value=None, key=f"milhas_{st.session_state.form_key}")
    folgas = st.number_input("Dias de Folga por Mês *", min_value=0, step=1, value=None, key=f"folgas_{st.session_state.form_key}")
    
    if milhas is not None and trailer is not None and rota is not None and folgas is not None:
        if trailer == "Dry Van": mult_trailer = 0.83
        elif trailer == "Flatbed": mult_trailer = 1.30
        elif trailer == "Reefer": mult_trailer = 1.10
        else: mult_trailer = 0
        
        if rota == "OTR": mult_rota = 1.20
        elif rota == "Regional": mult_rota = 0.90
        elif rota == "Local": mult_rota = 0.65
        else: mult_rota = 0
        
        previsao_calculada = (milhas * mult_trailer * mult_rota) * (1 - (folgas * 0.05))
        st.info(f"📊 **Previsão de Ganho do Sistema:** ${previsao_calculada:,.2f} por semana")
    else:
        st.info("📊 Preencha o Trailer, a Rota, as Milhas e as Folgas para visualizar a previsão automática de ganhos.")
    
    expectativa_ganho = st.number_input("Expectativa de Ganho Semanal ($) *", min_value=0.0, step=50.0, value=None, key=f"expectativa_{st.session_state.form_key}")
    
    st.write("Estado do Lead")
    empregado = st.checkbox("Atualmente Empregado (Company Driver)?", value=True, key=f"empregado_{st.session_state.form_key}")
    qualificou = st.checkbox("Qualificou para o Leasing?", value=False, key=f"qualificou_{st.session_state.form_key}")

st.markdown("---")
submit = st.button("Guardar Prospect na Base de Dados", type="primary")

if submit:
    estado_tratado = estado.upper()
    
    campos_faltantes = []
    if not nome: campos_faltantes.append("Nome do Motorista")
    if not estado: campos_faltantes.append("Estado")
    if anos_cdl is None: campos_faltantes.append("Tempo de CDL")
    if trailer is None: campos_faltantes.append("Tipo de Trailer")
    if rota is None: campos_faltantes.append("Rota Desejada")
    if dor_cliente is None: campos_faltantes.append("Principal Dor / Motivação")
    if milhas is None: campos_faltantes.append("Milhagem Semanal Média")
    if expectativa_ganho is None: campos_faltantes.append("Expectativa de Ganho Semanal")
    if folgas is None: campos_faltantes.append("Dias de Folga por Mês")

    if len(campos_faltantes) > 0:
        campos_str = ", ".join(campos_faltantes)
        st.error(f"⚠️ Operação bloqueada: Os seguintes campos são obrigatórios: **{campos_str}**.")
    elif estado_tratado not in ESTADOS_VALIDOS:
        st.error(f"⚠️ Operação bloqueada: A sigla '{estado_tratado}' não é válida. Insira uma sigla de 2 letras (ex: FL, TX).")
    else:
        try:
            with engine.connect() as conexao:
                query = text("""
                    INSERT INTO leads (nome, estado, anos_cdl, trailer, rota, dor_cliente, folgas, empregado, milhas, expectativa_ganho, qualificou)
                    VALUES (:nome, :estado, :anos, :trailer, :rota, :dor_cliente, :folgas, :empregado, :milhas, :expectativa, :qualificou)
                """)
                
                conexao.execute(query, {
                    "nome": nome, 
                    "estado": estado_tratado, 
                    "anos": anos_cdl, 
                    "trailer": trailer,
                    "rota": rota, 
                    "dor_cliente": dor_cliente,
                    "folgas": folgas, 
                    "empregado": empregado, 
                    "milhas": milhas,
                    "expectativa": expectativa_ganho, 
                    "qualificou": qualificou
                })
                conexao.commit()
            
            st.session_state["mensagem_sucesso"] = f"✅ Driver {nome} ({"Descartado" if qualificou == 0 else "Qualificado"}) foi guardado com sucesso na base de dados!"
            
            st.session_state.form_key += 1
            st.rerun()
            
        except Exception as e:
            st.error(f"Erro interno de ligação à base de dados: {e}")