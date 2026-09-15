
import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Evermat V6 — Digital Mass Balance", layout="wide")
try:
    password = st.secrets.get("APP_PASSWORD","")
except Exception:
    password = ""
if password:
    if st.sidebar.text_input("Senha", type="password") != password:
        st.stop()

st.title("Evermat V6 — Digital Mass Balance")
st.caption("REAL | CALCULADO | PROJETO | DESVIO — balanço auditável, sem fechamento silencioso.")

# Projeto Lucas E3 — transcrição do M&E balance
P = {
"corn":(52101,7294,0,0,44807,0.0,21.1),
"slurry":(142569,95211,301,0,47056,129.8,85.0),
"ferm_feed":(143836,94368,301,0,49166,130.6,33.3),
"ferm_co2":(16636,165,286,16185,0,0.0,32.2),
"beer":(130247,97668,17021,0,15558,129.1,68.9),
"scrub_btms":(19353,19066,286,0,0,19.4,32.2),
"co2_vent":(16662,165,1,16496,0,0.0,26.7),
"rect_btms":(11404,11390,14,0,0,11.4,61.4),
"rect_oh":(48028,3083,44945,0,0,59.1,106.1),
"whole_stillage":(121079,105507,14,0,15558,116.6,72.5),
"sieve_feed":(48017,3078,44939,0,0,59.1,102.8),
"thin_recycle":(86964,80873,10,0,6081,85.2,68.3),
"thin_evap":(22760,14110,3,0,8648,20.4,68.3),
"wet_cake":(15835,9755,1,0,6080,14.2,81.1),
"ddgs":(16366,1635,12,0,14718,0.0,93.3),
}
COLS=["Total","Água","Etanol","CO2","Sólidos","m3/h","T_C"]

st.sidebar.header("1. Alimentação / composição")
mode=st.sidebar.radio("Modo",["Simulação física","Caso-base Lucas E3"])
corn_tph = 52.101 if mode=="Caso-base Lucas E3" else st.sidebar.number_input("Moagem (t/h)",10.0,100.0,55.0,0.1)
moist = 14.0 if mode=="Caso-base Lucas E3" else st.sidebar.number_input("Umidade milho (%)",5.0,25.0,14.0,0.1)
starch_db=72.0 if mode=="Caso-base Lucas E3" else st.sidebar.number_input("Amido / MS (%)",40.0,85.0,72.0,0.1)
protein_db=8.8 if mode=="Caso-base Lucas E3" else st.sidebar.number_input("Proteína / MS (%)",0.0,20.0,8.8,0.1)
fiber_db=8.9 if mode=="Caso-base Lucas E3" else st.sidebar.number_input("Fibra / MS (%)",0.0,20.0,8.9,0.1)
oil_db=3.9 if mode=="Caso-base Lucas E3" else st.sidebar.number_input("Óleo / MS (%)",0.0,12.0,3.9,0.1)
sulf_db=1.0 if mode=="Caso-base Lucas E3" else st.sidebar.number_input("Sulfatos / MS (%)",0.0,5.0,1.0,0.1)
other_db=5.4 if mode=="Caso-base Lucas E3" else st.sidebar.number_input("Outros/cinzas / MS (%)",0.0,20.0,5.4,0.1)

st.sidebar.header("2. Processo — variáveis independentes")
slurry_sol=33.0 if mode=="Caso-base Lucas E3" else st.sidebar.number_input("Sólidos slurry (%)",20.0,45.0,33.0,0.1)
conv=st.sidebar.number_input("Conversão amido (%)",70.0,100.0,98.5,0.1, disabled=(mode=="Caso-base Lucas E3"))
ferm_eff=st.sidebar.number_input("Eficiência fermentativa (%)",70.0,100.0,94.0,0.1, disabled=(mode=="Caso-base Lucas E3"))
beer_sol=11.9 if mode=="Caso-base Lucas E3" else st.sidebar.number_input("Sólidos Beer medido/alvo (%)",5.0,20.0,11.9,0.1)

st.sidebar.header("3. Medições reais opcionais")
real_beer=st.sidebar.number_input("Beer FT-3420 (m³/h; 0=sem dado)",0.0,200.0,140.0,0.1)
real_beer_gl=st.sidebar.number_input("Beer (% v/v GL; 0=sem dado)",0.0,30.0,18.3,0.1)
real_whole=st.sidebar.number_input("Whole stillage (t/h; 0=sem dado)",0.0,200.0,0.0,0.1)
real_ddgs=st.sidebar.number_input("DDGS/WDG produto (t/h; 0=sem dado)",0.0,100.0,0.0,0.1)

st.sidebar.header("4. Contexto energético")
steam_barg=st.sidebar.number_input("Vapor processo (barg)",0.0,20.0,5.5,0.1)
steam_T=st.sidebar.number_input("Vapor processo (°C)",100.0,300.0,172.0,1.0)

corn=corn_tph*1000
water_corn=corn*moist/100
dry=corn-water_corn
comp_sum=starch_db+protein_db+fiber_db+oil_db+sulf_db+other_db
starch=dry*starch_db/100
protein=dry*protein_db/100
fiber=dry*fiber_db/100
oil=dry*oil_db/100
sulf=dry*sulf_db/100
other=dry*other_db/100

# Escala de projeto: referência independente
scale=corn/P["corn"][0]

# Modelo físico, quando não estamos no caso-base:
MWs=162.1406; MWw=18.01528; MWe2=92.13688; MWc2=88.019
converted=starch*conv/100
eth_theor=converted*MWe2/MWs
co2_theor=converted*MWc2/MWs
hydrolysis_water=converted*MWw/MWs
eth_calc=eth_theor*ferm_eff/100
# NÃO atribuir perda de eficiência a um componente sem dados
ferm_gap=eth_theor-eth_calc
conservative_solids=protein+fiber+oil+sulf+other+(starch-converted)

# Slurry calculado por sólidos totais
slurry_calc=dry/(slurry_sol/100)
slurry_added_water=max(0,slurry_calc-corn)

# Beer: no caso-base, reproduzimos o dado documental; na simulação,
# fecha por sólidos conservativos + teor de sólidos escolhido e mostra lacuna.
if mode=="Caso-base Lucas E3":
    beer_mass=P["beer"][0]
    beer_m3=P["beer"][5]
    beer_water=P["beer"][1]
    beer_eth=P["beer"][2]
    beer_solids=P["beer"][4]
    beer_co2=0.0
    co2_calc=P["ferm_co2"][3]
else:
    beer_solids=conservative_solids
    beer_mass=beer_solids/(beer_sol/100)
    beer_eth=eth_calc
    beer_water=beer_mass-beer_solids-beer_eth
    density_proj=P["beer"][0]/P["beer"][5]
    beer_m3=beer_mass/density_proj
    beer_co2=0.0
    co2_calc=co2_theor

# Projeto escalado para comparação
def proj(key, idx=0): return P[key][idx]*scale

def deviation(calc, project):
    return (calc/project-1)*100 if project else float("nan")

tabs=st.tabs(["Executive", "Milho → Beer", "Mapa de correntes", "Fechamento por área", "Real × Calc × Projeto", "Auditoria"])

with tabs[0]:
    a,b,c,d,e=st.columns(5)
    a.metric("Moagem",f"{corn/1000:.2f} t/h")
    b.metric("Beer calculada",f"{beer_m3:.1f} m³/h")
    c.metric("Etanol na Beer",f"{beer_eth/1000:.2f} t/h")
    d.metric("CO₂ fermentação",f"{co2_calc/1000:.2f} t/h")
    e.metric("Sólidos Beer",f"{beer_solids/beer_mass*100:.2f}%")
    st.subheader("Semáforo do modelo")
    if abs(comp_sum-100)<=0.2: st.success(f"Composição MS = {comp_sum:.1f}% — OK")
    else: st.error(f"Composição MS = {comp_sum:.1f}% — não fecha 100%")
    if mode=="Caso-base Lucas E3":
        st.success("Modo validação: valores documentais críticos do Lucas E3 preservados.")
    else:
        st.warning("Simulação: a parcela de ineficiência fermentativa permanece NÃO RECONCILIADA até termos açúcares residuais/byproducts medidos.")
    st.caption(f"Vapor registrado para a futura camada energética: {steam_barg:.1f} barg / {steam_T:.0f} °C.")

with tabs[1]:
    data=[
      ["Milho",corn,water_corn,0,0,dry,"ENTRADA/CALC"],
      ["Corn slurry",slurry_calc,slurry_calc-dry,0,0,dry,"CALCULADO"],
      ["Amido convertido",converted,hydrolysis_water,0,0,converted,"REAÇÃO"],
      ["Etanol teórico",eth_theor,0,eth_theor,0,0,"REAÇÃO"],
      ["CO₂ teórico",co2_theor,0,0,co2_theor,0,"REAÇÃO"],
      ["Beer",beer_mass,beer_water,beer_eth,0,beer_solids,"CALCULADO/PROJETO"],
    ]
    df=pd.DataFrame(data,columns=["Corrente/termo","Total kg/h","Água kg/h","Etanol kg/h","CO₂ kg/h","Sólidos/termo kg/h","Classe"])
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.write(f"Água adicionada calculada ao slurry: **{slurry_added_water/1000:.2f} t/h**")
    st.write(f"Água estequiométrica de hidrólise: **{hydrolysis_water/1000:.2f} t/h**")
    st.write(f"Gap fermentativo não atribuído: **{ferm_gap/1000:.2f} t/h equivalente de etanol teórico**")

with tabs[2]:
    labels={
      "corn":"1501 Incoming Corn","slurry":"3109 Corn Slurry","ferm_feed":"3407 Fermentation Feed",
      "ferm_co2":"3450 Fermenter CO₂","beer":"3434 Beer Feed","scrub_btms":"6506 CO₂ Scrubber Bottoms",
      "co2_vent":"4610 CO₂ Vent","rect_btms":"6231 Rectifier Bottoms","rect_oh":"6243 Rectifier Overheads",
      "whole_stillage":"6111 Beer Still Bottoms / Whole Stillage","sieve_feed":"6242 Sieve Feed",
      "thin_recycle":"7113 Thin Stillage Recycle","thin_evap":"7114 Thin Stillage to Evap",
      "wet_cake":"7220 Centrifuge Wet Cake","ddgs":"7537 DDGS Product"
    }
    rows=[]
    for k,v in labels.items():
        t,w,et,c,s,q,T=P[k]
        rows.append([v,t,w,et,c,s,q,T,(w+et+c+s)-t])
    st.dataframe(pd.DataFrame(rows,columns=["Corrente","Total kg/h","Água","Etanol","CO₂","Sólidos","m³/h","°C","Erro componentes kg/h"]),
                 use_container_width=True,hide_index=True)

with tabs[3]:
    # Valores de Summary Table do documento
    areas=[
      ("Slurry Mixing",151876,151695),
      ("Starch Conversion",147260,147256),
      ("Fermentation",147302,146883),
      ("CO₂ Scrubber",35702,36015),
      ("Distillation",246763,246212),
      ("Ethanol Dehydration",42569,42208),
      ("Vapor Condenser",161750,161467),
      ("Evaporation",119540,119318),
      ("Stillage Processing",121760,121583),
      ("DDGS Drying",99127,99127),
    ]
    out=[]
    for name,mi,mo in areas:
        err=mi-mo
        closure=mo/mi*100
        out.append([name,mi,mo,err,closure])
    st.dataframe(pd.DataFrame(out,columns=["Área","Mass In kg/h","Mass Out kg/h","Δ kg/h","Fechamento %"]),
                 use_container_width=True,hide_index=True)
    st.caption("Fechamentos acima são os valores do caso-base documental, não medições atuais.")

with tabs[4]:
    rows=[
      ["Beer m³/h", real_beer if real_beer else None, beer_m3, proj("beer",5)],
      ["Beer total t/h", None, beer_mass/1000, proj("beer")/1000],
      ["Etanol Beer t/h", None, beer_eth/1000, proj("beer",2)/1000],
      ["CO₂ fermentação t/h", None, co2_calc/1000, proj("ferm_co2",3)/1000],
      ["Whole stillage t/h", real_whole if real_whole else None, None, proj("whole_stillage")/1000],
      ["DDGS/WDG t/h", real_ddgs if real_ddgs else None, None, proj("ddgs")/1000],
    ]
    df=pd.DataFrame(rows,columns=["Variável","REAL","CALCULADO","PROJETO"])
    df["Desvio Calc-Projeto %"]=(df["CALCULADO"]/df["PROJETO"]-1)*100
    df["Desvio Real-Calc %"]=(df["REAL"]/df["CALCULADO"]-1)*100
    st.dataframe(df,use_container_width=True,hide_index=True)
    if real_beer and beer_m3:
        st.metric("FT-3420 vs modelo",f"{real_beer:.1f} m³/h",f"{(real_beer/beer_m3-1)*100:+.2f}% vs calculado")

with tabs[5]:
    st.subheader("Regras de integridade")
    st.markdown("""
- **Projeto** nunca é sobrescrito por medição.
- **Real** nunca é usado silenciosamente para forçar o calculado.
- **Calculado** vem das equações e hipóteses declaradas.
- **Não reconciliado** permanece visível até existir dado que permita atribuição física.
- Fechamento é mostrado por **massa total e componente**, quando o documento suporta o componente.
- GL, % massa e sólidos não são tratados como grandezas intercambiáveis.
""")
    st.subheader("Dados ainda necessários para elevar a precisão")
    st.write("Açúcares residuais/DP, definição laboratorial de sólidos, água e reciclos reais para slurry/fermentação, composição de whole/thin stillage, wet cake, CDS, óleo e produto final. Sem esses dados, a V6 não inventa a distribuição.")
    st.subheader("Composição do milho")
    st.dataframe(pd.DataFrame([
        ["Umidade (base úmida)",moist],["Amido / MS",starch_db],["Proteína / MS",protein_db],
        ["Fibra / MS",fiber_db],["Óleo / MS",oil_db],["Sulfatos / MS",sulf_db],["Outros/cinzas / MS",other_db],
    ],columns=["Parâmetro","%"]),use_container_width=True,hide_index=True)

st.divider()
st.caption("Evermat V6 — Digital Mass Balance | Motor auditável. Uso de engenharia; não é sistema de controle.")
