
import math
import pandas as pd
import streamlit as st
try:
    from iapws import IAPWS97
    IAPWS_OK = True
except Exception:
    IAPWS_OK = False

st.set_page_config(page_title="Evermat | Balanço Massa & Energia V4", layout="wide")

def check_password():
    if "APP_PASSWORD" not in st.secrets:
        return True
    if st.session_state.get("password_correct", False):
        return True
    st.title("Evermat — Balanço de Massa & Energia")
    pwd = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if pwd == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        st.error("Senha incorreta.")
    return False
if not check_password(): st.stop()

def safe(a,b): return a/b if b else float("nan")
def tsat(p_barg):
    if not IAPWS_OK: return None
    return IAPWS97(P=(p_barg+1.01325)/10, x=1).T-273.15

st.title("Evermat — Balanço de Massa & Energia | V4")
st.caption("Modelo interativo: Operação Real + Simulação física. MEDIDO ≠ CALCULADO ≠ ESTIMADO.")

mode = st.sidebar.radio("Modo do modelo", ["Operação Real", "Simulação física"], horizontal=False)

st.sidebar.header("Milho / Fermentação")
corn = st.sidebar.number_input("Moagem de milho [t/h]", 1.0, 100.0, 55.0, 0.5)
moist = st.sidebar.number_input("Umidade do milho [% m/m]", 5.0, 25.0, 13.5, 0.1)
starch_dry = st.sidebar.number_input("Amido na matéria seca [% m/m]", 50.0, 80.0, 70.0, 0.5)
conv = st.sidebar.number_input("Conversão do amido [%]", 80.0, 100.0, 96.0, 0.1)
ferm = st.sidebar.number_input("Eficiência fermentativa [%]", 80.0, 100.0, 95.0, 0.1)

dry_corn = corn*(1-moist/100)
starch = dry_corn*starch_dry/100
nonstarch = dry_corn-starch
starch_conv = starch*conv/100
# C6H10O5 + H2O -> 2 C2H5OH + 2 CO2
eth_theor = starch_conv*(92.136/162.141)
co2_theor = starch_conv*(88.02/162.141)
eth = eth_theor*ferm/100
# unconverted/side-products retained in beer solids on simplified dry basis
residual_solids = nonstarch + (starch-starch_conv) + (eth_theor-eth)

if mode == "Operação Real":
    beer_m3h = st.sidebar.number_input("Beer medida [m³/h]", 1.0, 300.0, 140.0, 1.0)
    beer_gl = st.sidebar.number_input("Beer medida [GL %v/v]", 1.0, 30.0, 18.3, 0.1)
    beer_solids = st.sidebar.number_input("Sólidos Beer medidos [% m/m]", 1.0, 30.0, 10.0, 0.1)
    beer_density = st.sidebar.number_input("Densidade Beer [t/m³]", 0.85, 1.15, 0.99, 0.005)
    beer_mass = beer_m3h*beer_density
    water_beer = max(beer_mass-eth-residual_solids,0)
    water_added = max(water_beer - corn*moist/100, 0)
else:
    beer_solids = st.sidebar.number_input("Sólidos alvo na Beer [% m/m]", 1.0, 30.0, 10.0, 0.1)
    beer_density = st.sidebar.number_input("Densidade Beer [t/m³]", 0.85, 1.15, 0.99, 0.005)
    # Beer solids concentration closes total beer mass from residual dry solids.
    beer_mass = residual_solids/(beer_solids/100)
    beer_m3h = beer_mass/beer_density
    water_beer = max(beer_mass-eth-residual_solids,0)
    water_added = max(water_beer - corn*moist/100,0)
    beer_gl = safe((eth*1000/789.0), beer_m3h)*100

st.sidebar.header("Energia / Destilação")
beer_t = st.sidebar.number_input("Temperatura Beer [°C]", 20.0, 90.0, 67.6, 0.5)
hx_flow = st.sidebar.number_input("Vapor HX-6225 [t/h]", 0.0, 80.0, 30.0, 0.5)
hx_p = st.sidebar.number_input("Pressão vapor HX [barg]", 0.1, 15.0, 5.41, 0.05)
hx_t = st.sidebar.number_input("Temperatura vapor HX [°C]", 100.0, 230.0, 170.0, 0.5)
cond_t = st.sidebar.number_input("Condensado HX [°C]", 50.0, 190.0, 140.0, 0.5)
vent = st.sidebar.number_input("Vent VP-6250 [t/h]", 0.0, 20.0, 5.4, 0.1)
boiler = st.sidebar.number_input("Vapor caldeira [t/h]", 0.0, 120.0, 60.0, 1.0)
turbine_flow = st.sidebar.number_input("Vapor turbina [t/h]", 0.0, 100.0, 39.0, 1.0)
turbine_mw = st.sidebar.number_input("Potência turbina [MW]", 0.0, 20.0, 6.0, 0.1)

aa_lpt = safe(eth*1000/0.789, corn*1000) * 1000
co2_actual = st.sidebar.number_input("CO₂ medido [t/h] (0 = faltante)", 0.0, 50.0, 0.0, 0.1)

hx_duty = None; hx_sat=None; superheat=None
if IAPWS_OK and hx_flow>0:
    p=(hx_p+1.01325)/10
    hin=IAPWS97(P=p,T=hx_t+273.15).h
    hout=IAPWS97(T=cond_t+273.15,x=0).h
    hx_duty=hx_flow/3.6*(hin-hout)/1000
    hx_sat=tsat(hx_p); superheat=hx_t-hx_sat

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Moagem", f"{corn:.1f} t/h")
c2.metric("Beer", f"{beer_m3h:.1f} m³/h", "calculada" if mode=="Simulação física" else "medida")
c3.metric("Sólidos Beer", f"{beer_solids:.1f}%")
c4.metric("Beer GL", f"{beer_gl:.2f}")
c5.metric("EtOH AA", f"{aa_lpt:.1f} L/t milho")
c6.metric("CO₂ teórico", f"{co2_theor:.2f} t/h")

tabs=st.tabs(["Painel","Milho → Beer","Balanço de massa","Energia","Cenários","Qualidade dos dados","CSV"])

with tabs[0]:
    st.subheader("Painel executivo")
    st.success(f"Modo ativo: {mode}")
    a,b,c=st.columns(3)
    a.metric("Matéria seca do milho",f"{dry_corn:.2f} t/h")
    a.metric("Amido",f"{starch:.2f} t/h")
    b.metric("Etanol calculado",f"{eth:.2f} t/h")
    b.metric("CO₂ estequiométrico",f"{co2_theor:.2f} t/h")
    c.metric("Água adicional implícita",f"{water_added:.2f} t/h")
    c.metric("Beer / milho",f"{safe(beer_m3h,corn):.3f} m³/t")
    st.info("No modo Simulação física, a Beer não é um slider independente: ela fecha a partir da moagem, composição/conversão e sólidos alvo. No modo Operação Real, Beer e sólidos são medições e o app calcula a inconsistência do balanço.")

with tabs[1]:
    st.subheader("Motor físico Milho → Beer")
    df=pd.DataFrame([
        ["Milho úmido",corn,"t/h","MEDIDO"],
        ["Água no milho",corn*moist/100,"t/h","CALCULADO"],
        ["Matéria seca",dry_corn,"t/h","CALCULADO"],
        ["Amido",starch,"t/h","ESTIMADO/ANÁLISE"],
        ["Amido convertido",starch_conv,"t/h","CALCULADO"],
        ["Etanol",eth,"t/h","CALCULADO"],
        ["CO₂ estequiométrico",co2_theor,"t/h","CALCULADO"],
        ["Sólidos residuais simplificados",residual_solids,"t/h","CALCULADO"],
        ["Água na Beer",water_beer,"t/h","CALCULADO"],
        ["Beer total",beer_mass,"t/h","CALCULADO" if mode=="Simulação física" else "MEDIDO"],
        ["Beer volume",beer_m3h,"m³/h","CALCULADO" if mode=="Simulação física" else "MEDIDO"],
    ],columns=["Variável","Valor","Unidade","Origem"])
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.warning("O fechamento atual trata proteína/fibra/óleo/cinzas como sólidos residuais agregados. Para fechar copro­dutos individualmente serão necessárias análises reais de composição do milho e correntes.")

with tabs[2]:
    st.subheader("Fechamento de massa")
    mass_in = corn + water_added
    mass_out = beer_mass + co2_theor
    err=100*(mass_in-mass_out)/mass_in if mass_in else float("nan")
    x,y,z=st.columns(3)
    x.metric("Entrada",f"{mass_in:.2f} t/h")
    y.metric("Saída",f"{mass_out:.2f} t/h")
    z.metric("Erro fechamento",f"{err:.2f}%")
    st.caption("Este fechamento cobre o bloco Milho + água → Beer + CO₂. Correntes auxiliares/enzimas/químicos não foram incluídas enquanto não forem informadas.")

with tabs[3]:
    st.subheader("Energia")
    e1,e2,e3=st.columns(3)
    e1.metric("HX-6225 duty",f"{hx_duty:.2f} MWt" if hx_duty is not None else "N/D")
    e2.metric("Tsat HX",f"{hx_sat:.1f} °C" if hx_sat is not None else "N/D")
    e3.metric("Superaquecimento",f"{superheat:.1f} °C" if superheat is not None else "N/D")
    st.metric("Turbina",f"{safe(turbine_mw*1000,turbine_flow):.1f} kWh/t vapor")
    st.metric("Vapor específico / EtOH calculado",f"{safe(boiler*1000,eth*1000/0.789):.2f} kg/L AA")

with tabs[4]:
    st.subheader("Cenário interativo")
    sim_corn=st.slider("Moagem [t/h]",30.0,75.0,float(corn),0.5)
    sim_sol=st.slider("Sólidos Beer [%]",5.0,20.0,float(beer_solids),0.1)
    ratio=sim_corn/corn
    sim_residual=residual_solids*ratio
    sim_eth=eth*ratio
    sim_mass=sim_residual/(sim_sol/100)
    sim_vol=sim_mass/beer_density
    sim_gl=safe(sim_eth*1000/789.0,sim_vol)*100
    q1,q2,q3=st.columns(3)
    q1.metric("Beer calculada",f"{sim_vol:.1f} m³/h")
    q2.metric("Beer GL calculado",f"{sim_gl:.2f}")
    q3.metric("Etanol",f"{sim_eth:.2f} t/h")
    st.caption("Aqui moagem e sólidos realmente alteram a vazão de Beer. Cenário é análise de sensibilidade, não instrução operacional.")

with tabs[5]:
    st.subheader("Qualidade dos dados")
    rows=[
        ["Moagem","MEDIDO"],
        ["Umidade milho","MEDIDO/ANÁLISE"],
        ["Amido base seca","ESTIMADO/ANÁLISE"],
        ["Conversão amido","ESTIMADO até medição"],
        ["Eficiência fermentativa","ESTIMADO até fechamento"],
        ["Sólidos Beer","MEDIDO" if mode=="Operação Real" else "ALVO"],
        ["Densidade Beer","ESTIMADO até correlação/medição"],
        ["CO₂","MEDIDO" if co2_actual>0 else "FALTANTE"],
        ["Vapor HX-6225","ESTIMADO" if hx_flow else "FALTANTE"],
    ]
    st.dataframe(pd.DataFrame(rows,columns=["Dado","Status"]),use_container_width=True,hide_index=True)
    st.warning("O app não força fechamento ajustando silenciosamente medições. Dados faltantes permanecem identificados.")

with tabs[6]:
    st.subheader("Exportar snapshot")
    snap=pd.DataFrame({
        "tag":["corn_tph","corn_moist_pct","starch_dry_pct","conversion_pct","ferm_eff_pct","beer_solids_pct","beer_m3h","beer_gl","ethanol_tph","co2_tph_calc","water_added_tph","hx_duty_mw"],
        "value":[corn,moist,starch_dry,conv,ferm,beer_solids,beer_m3h,beer_gl,eth,co2_theor,water_added,hx_duty]
    })
    st.dataframe(snap,use_container_width=True,hide_index=True)
    st.download_button("Baixar CSV",snap.to_csv(index=False).encode("utf-8-sig"),"evermat_v4_snapshot.csv","text/csv")
