import pandas as pd
import random
import time
import schedule
from faker import Faker
from sqlalchemy import create_engine
from datetime import datetime, timedelta

fake = Faker('en_US')
STRING_CONEXAO = "mysql+pymysql://root:Marry79513.@localhost:3306/leasing_prospects"
engine = create_engine(STRING_CONEXAO)

ESTADOS_VALIDOS = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

WEST = ["CA", "OR", "WA", "AK", "HI", "NV", "ID", "UT", "MT", "WY", "CO"]
SOUTHWEST = ["AZ", "NM", "TX", "OK"]
MIDWEST = ["IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"]
NORTHEAST = ["CT", "ME", "MA", "NH", "NJ", "NY", "PA", "RI", "VT", "DE", "MD"]
SOUTHEAST = ["AL", "FL", "GA", "KY", "MS", "NC", "SC", "TN", "VA", "WV", "AR", "LA"]

TRAILERS = ["Dry Van", "Flatbed", "Reefer"]
ROTAS = ["OTR", "Regional", "Local"]
DORES = ["Mais dinheiro/milhas", "Equipamento", "Comunicação", "Mais folga", "Outros"]
PESOS_DORES = [0.51, 0.15, 0.10, 0.19, 0.05]

def injetar_novos_leads():
    qtd_leads = random.randint(0, 500)
    print(f"\n[{time.strftime('%H:%M:%S')}] Iniciando injeção de {qtd_leads} novo(s) lead(s)...")
    
    dados = []
    agora = datetime.now()
    
    for _ in range(qtd_leads):
        # 1. Geração de Data Aleatória Histórica (até 360 dias atrás)
        dias_atras = random.randint(0, 360)
        horas = random.randint(8, 18)
        minutos = random.randint(0, 59)
        segundos = random.randint(0, 59)
        
        data_base = agora - timedelta(days=dias_atras)
        data_hora_final = data_base.replace(hour=horas, minute=minutos, second=segundos, microsecond=0)
        
        fator_tempo = (dias_atras - 180) / 180  
        
        # 2. Pesos de Estado Dinâmicos
        pesos_estados = []
        for uf in ESTADOS_VALIDOS:
            peso_uf = 100 
            
            if uf in WEST or uf in SOUTHWEST:
                peso_uf += (140 * fator_tempo)
            elif uf in MIDWEST or uf in SOUTHEAST:
                peso_uf -= (20 * fator_tempo)
                
            if uf in ["TX", "CA"]:
                peso_uf += 75
            
            pesos_estados.append(max(peso_uf, 5)) 
        
        estado = random.choices(ESTADOS_VALIDOS, weights=pesos_estados)[0]
        dor = random.choices(DORES, weights=PESOS_DORES)[0]
        anos_cdl = random.randint(0, 40)
        empregado = random.choices([True, False], weights=[0.65, 0.35])[0]
        
        peso_otr = 45
        peso_reg = 30
        peso_loc = 25
        
        # 3. Viés da Dor na Rota
        if dor == "Mais dinheiro/milhas":
            peso_otr += 20
            peso_reg -= 5
            peso_loc -= 5
        elif dor == "Mais folga":
            peso_loc += 15
            peso_reg += 15
            peso_otr -= 15
        
        peso_van = 55
        peso_flat = 20
        peso_reef = 25
        
        # 4. Viés da Experiência (Anos de CDL)
        if anos_cdl > 0:
            fator = min(anos_cdl, 25)
            peso_otr -= fator * 1.5
            peso_reg += fator
            peso_loc += fator * 0.5
            peso_flat -= fator * 1.2
            peso_van += fator * 0.6
            peso_reef += fator * 0.6

        # 5. Viés Geográfico Geral
        if estado in WEST:
            peso_otr -= 20
            peso_reg += 15
            peso_loc += 15
            peso_van += 30
            peso_reef += 35
        elif estado in SOUTHWEST:
            peso_reef += 25
            peso_flat += 30
        elif estado in MIDWEST:
            peso_van += 25
            peso_reef += 30
            peso_flat += 20
        elif estado in NORTHEAST:
            peso_van += 40
        elif estado in SOUTHEAST:
            peso_flat += 35
        
        if estado in ["TX", "FL", "CA", "PA"]:
            peso_otr += 10
            
        peso_otr = max(peso_otr, 5)
        peso_loc = max(peso_loc, 5)
        peso_flat = max(peso_flat, 5)
        peso_van = max(peso_van, 5)
        peso_reef = max(peso_reef, 5)

        rota = random.choices(ROTAS, weights=[peso_otr, peso_reg, peso_loc])[0]
        trailer = random.choices(TRAILERS, weights=[peso_van, peso_flat, peso_reef])[0]
        
        if rota == 'OTR':
            milhas = random.randint(2500, 3000)
            folgas = random.randint(2, 6)
            mult_rota = 1.20
        elif rota == 'Regional':
            milhas = random.randint(1500, 2000)
            folgas = random.randint(6, 10)
            mult_rota = 0.90
        else:
            milhas = random.randint(400, 600)
            folgas = random.randint(2, 3)
            mult_rota = 0.65
            
        if trailer == "Dry Van": mult_trailer = 0.83
        elif trailer == "Flatbed": mult_trailer = 1.30
        else: mult_trailer = 1.10
        
        previsao_python = (milhas * mult_trailer * mult_rota) * (1 - (folgas * 0.05))
        
        expectativa_base = random.triangular(1000, 2500, 1300)
        multiplicador_experiencia = 1 + (anos_cdl * random.uniform(0.02, 0.04))
        expectativa = expectativa_base * multiplicador_experiencia
        
        if rota == 'OTR':
            expectativa *= 1.20
        elif rota == 'Local':
            expectativa *= 0.80

        if not empregado:
            expectativa *= 0.80

        # 6. Viés de Custo de Vida
        if estado in NORTHEAST:
            expectativa *= 1.20
        elif estado in MIDWEST:
            expectativa *= 0.80
            
        expectativa = round(expectativa, 2)
        
        ratio = previsao_python / expectativa if expectativa > 0 else 0

        if ratio <= 0.5:
            p_qual = 0.0
        elif ratio <= 1.0:
            p_qual = ratio - 0.5
        elif ratio < 2.0:
            p_qual = 0.5 * ratio
        else:
            p_qual = 1.0

        if not empregado:
            p_qual = min(1.0, p_qual + 0.25)

        qualificou = random.random() < p_qual

        if dias_atras > 240:
            if not empregado:
                qualificou = False
        else:
            if anos_cdl < 1 or anos_cdl > 30:
                qualificou = False
                
        # 7. Regra Estrita de Desqualificação Geográfica
        if estado in ["HI", "AK"]:
            qualificou = False
            
        nome_falso = fake.name()
                
        dados.append({
            "nome": nome_falso,
            "estado": estado,
            "anos_cdl": anos_cdl,
            "trailer": trailer,
            "rota": rota,
            "dor_cliente": dor,
            "folgas": folgas,
            "empregado": empregado,
            "milhas": milhas,
            "expectativa_ganho": expectativa,
            "qualificou": qualificou,
            "criado_em": data_hora_final
        })
        print(f" -> Gerado: {nome_falso} ({estado}) - Trailer: {trailer} - Rota: {rota}")

    try:
        df_leads = pd.DataFrame(dados)
        df_leads.to_sql(name='leads', con=engine, if_exists='append', index=False)
        print("✅ Lote salvo no banco com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")

schedule.every(5).seconds.do(injetar_novos_leads)

print("Robô de Injeção Iniciado. Rodando a cada 30 segundos. Pressione Ctrl+C para parar.")

while True:
    schedule.run_pending()
    time.sleep(1)