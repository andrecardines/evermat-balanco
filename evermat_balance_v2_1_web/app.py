
import pandas as pd
import streamlit as st

try:
    from iapws import IAPWS97
    IAPWS_OK = True
except Exception:
    IAPWS_OK = False

st.set_page_config(page_title="Evermat | Balanço Massa & Energia V2.1", layout="wide")

# ---------------------------
# Acesso privado (Streamlit Secrets)
# ---------------------------
def check_password():
    configured = "APP_PASSWORD" in st.secrets
    if not configured:
        st.warning("APP_PASSWORD não configurada. Em produção, configure a senha nas Secrets do Streamlit Cloud.")
        return True
    if st.session_state.get("password_correct", False):
        return True
    st.title("Evermat — Balanço de Massa & Energia")
    st.caption("Acesso restrito")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar", use_container_width=True):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    return False

if not check_password():
    st.stop()

ATM_BAR = 1.01325

def barg_to_mpa(p_barg):
    return (p_barg + ATM_BAR)/10.0

def steam_h_pt(p_barg, t_c):
    if not IAPWS_OK:
        return float("nan")
    return IAPWS97(P=barg_to_mpa(p_barg), T=t_c+273.15).h

def sat_from_barg(p_barg):
    if not IAPWS_OK:
        return (float("nan"),)*4
    p = barg_to_mpa(p_barg)
    wl = IAPWS97(P=p, x=0)
    wv = IAPWS97(P=p, x=1)
    return wl.T-273.15, wl.h, wv.h, wv.h-wl.h

def sat_from_temp(t_c):
    if not IAPWS_OK:
        return (float("nan"),)*4
    wl = IAPWS97(T=t_c+273.15, x=0)
    wv = IAPWS97(T=t_c+273.15, x=1)
    return wl.P*10.0, wl.h, wv.h, wv.h-wl.h

def h_liq(t_c):
    if IAPWS_OK and 0 < t_c < 373.8:
        return IAPWS97(T=t_c+273.15, x=0).h
    return 4.186*t_c

def mw_from_tph_dh(tph, dh):
    return tph*dh/3.6/1000.0

def status_chip(kind):
    return {"MEDIDO":"🟢 MEDIDO", "CALCULADO":"🔵 CALCULADO", "ESTIMADO":"🟠 ESTIMADO"}.get(kind, kind)

st.sidebar.title("Evermat — V2")
st.sidebar.caption("Base técnica editável. Não força fechamento quando faltam dados.")

with st.sidebar.expander("1) Moagem / Fermentação", expanded=True):
    corn_tph = st.number_input("Moagem milho [t/h]", 0.0, 100.0, 53.0, 0.1)
    corn_moist = st.number_input("Umidade milho [% m/m]", 0.0, 30.0, 13.5, 0.1)
    beer_m3h = st.number_input("Cerveja p/ Beer Column [m³/h]", 0.0, 250.0, 140.0, 0.1)
    beer_gl = st.number_input("Cerveja [GL %v/v]", 0.0, 30.0, 18.3, 0.1)
    beer_t_c = st.number_input("T cerveja entrada [°C]", 0.0, 100.0, 67.6, 0.1)
    beer_rho = st.number_input("Densidade cerveja [t/m³] — estimada", 0.80, 1.20, 0.97, 0.005)
    beer_cp = st.number_input("Cp cerveja [kJ/kg.K] — estimado", 3.0, 5.0, 4.0, 0.01)

with st.sidebar.expander("2) Beer Column / Retificação"):
    beer_over_gl = st.number_input("Saída Beer Column → R1 [GL]", 1.0, 95.0, 60.0, 0.5)
    etoh_recovery = st.number_input("Recuperação EtOH até R1 [%]", 80.0, 100.0, 99.0, 0.1)
    r1_bottom_c = st.number_input("Base VP-6225 [°C]", 100.0, 170.0, 146.0, 0.5)
    r1_pressure_barg = st.number_input("Pressão VP-6225 [barg]", 0.0, 10.0, 3.44, 0.01)
    r1_reflux_m3h = st.number_input("Refluxo R1 [m³/h]", 0.0, 150.0, 82.0, 1.0)
    r1_recirculation_m3h = st.number_input("Recirculação PC-6225 [m³/h]", 0.0, 2000.0, 750.0, 10.0)

with st.sidebar.expander("3) HX-6225"):
    hx_p_barg = st.number_input("Vapor HX-6225 [barg]", 0.0, 15.0, 5.41, 0.01)
    hx_t_c = st.number_input("T vapor HX-6225 [°C]", 100.0, 250.0, 170.0, 0.1)
    hx_steam_tph = st.number_input("Vazão vapor HX-6225 [t/h] — estimada/medida", 0.0, 60.0, 30.0, 0.5)
    hx_cond_t_c = st.number_input("T condensado saída HX [°C]", 80.0, 180.0, 140.0, 0.5)

with st.sidebar.expander("4) VP-6250 / Evaporação"):
    vp6250_t_c = st.number_input("VP-6250 [°C]", 70.0, 120.0, 102.0, 0.1)
    vp6250_level = st.number_input("Nível VP-6250 [%]", 0.0, 100.0, 53.0, 0.5)
    evap_e1_cond_m3h = st.number_input("Condensado 1º efeito [m³/h]", 0.0, 100.0, 26.1, 0.1)
    vent_tph = st.number_input("Vapor p/ atmosfera [t/h] — estimado", 0.0, 20.0, 5.4, 0.1)

with st.sidebar.expander("5) Caldeira / Turbina"):
    boiler_tph = st.number_input("Caldeira [t/h]", 0.0, 100.0, 60.0, 0.5)
    boiler_p_bara = st.number_input("Caldeira [bar(a)]", 1.0, 100.0, 67.0, 0.5)
    boiler_t_c = st.number_input("Caldeira [°C]", 100.0, 600.0, 510.0, 1.0)
    turbine_tph = st.number_input("Vapor turbina [t/h]", 0.0, 100.0, 39.0, 0.5)
    turbine_mw = st.number_input("Potência turbina [MW]", 0.0, 20.0, 6.0, 0.1)

corn_dry_tph = corn_tph*(1-corn_moist/100)
beer_etoh_m3h = beer_m3h*beer_gl/100
r1_abs_etoh_m3h = beer_etoh_m3h*etoh_recovery/100
r1_feed_m3h = r1_abs_etoh_m3h/(beer_over_gl/100) if beer_over_gl > 0 else 0.0
r1_water_m3h = max(0.0, r1_feed_m3h-r1_abs_etoh_m3h)

if IAPWS_OK:
    hx_tsat, hx_hf, hx_hg, hx_hfg = sat_from_barg(hx_p_barg)
    hx_hin = steam_h_pt(hx_p_barg, hx_t_c)
    hx_hcond = h_liq(hx_cond_t_c)
    hx_duty_mw = mw_from_tph_dh(hx_steam_tph, hx_hin-hx_hcond)
    superheat = hx_t_c-hx_tsat
    vp_p_bara, vp_hf, vp_hg, vp_hfg = sat_from_temp(vp6250_t_c)
    flash_frac = max(0.0, min(1.0, (hx_hcond-vp_hf)/vp_hfg))
    flash_tph = hx_steam_tph*flash_frac
    vent_mw = mw_from_tph_dh(vent_tph, vp_hfg)
else:
    hx_tsat=hx_hf=hx_hg=hx_hfg=hx_hin=hx_hcond=hx_duty_mw=superheat=float("nan")
    vp_p_bara=vp_hf=vp_hg=vp_hfg=flash_frac=flash_tph=vent_mw=float("nan")

beer_mass_kgh = beer_m3h*beer_rho*1000
q_to_45_mw = beer_mass_kgh*beer_cp*max(0, beer_t_c-45)/3600/1000
q_to_45_tph_eq = q_to_45_mw*3600/vp_hfg if IAPWS_OK else float("nan")
specific_elec_kwh_per_tsteam = turbine_mw*1000/turbine_tph if turbine_tph > 0 else float("nan")
beer_per_corn = beer_m3h/corn_tph if corn_tph > 0 else float("nan")
etoh_abs_l_per_tcorn = beer_etoh_m3h*1000/corn_tph if corn_tph > 0 else float("nan")

st.title("Evermat — Balanço de Massa & Energia | V2.1 Web")
st.caption("Fluxograma operacional + balanços + qualidade dos dados + cenários. Água/vapor via IAPWS-IF97.")

if not IAPWS_OK:
    st.error("Pacote iapws ausente. Rode: pip install -r requirements.txt")

tabs = st.tabs(["PFD", "Balanço de massa", "Balanço de energia", "Cenários", "Qualidade dos dados", "Premissas"])

with tabs[0]:
    st.subheader("Fluxograma térmico simplificado")
    dot = f"""
    digraph G {{
      rankdir=LR;
      graph [bgcolor="transparent", pad="0.2", nodesep="0.45", ranksep="0.65"];
      node [shape=box, style="rounded,filled", fillcolor="#F7F7F7", fontname="Arial"];
      edge [fontname="Arial", fontsize=10];
      Corn [label="Milho\\n{corn_tph:.1f} t/h"];
      Fermentation [label="Fermentação\\nBeer {beer_m3h:.1f} m³/h\\n{beer_gl:.1f} GL"];
      BeerCol [label="Beer Column\\nFeed {beer_m3h:.1f} m³/h\\nOverhead {beer_over_gl:.1f} GL"];
      R1 [label="VP-6225 / R1\\nBase {r1_bottom_c:.1f} °C\\nRefluxo {r1_reflux_m3h:.0f} m³/h"];
      HX [label="HX-6225\\n{hx_p_barg:.2f} barg\\n{hx_t_c:.1f} °C"];
      VP [label="VP-6250\\n{vp6250_t_c:.1f} °C\\nNível {vp6250_level:.0f}%"];
      Evap [label="Evaporação\\nCond. E1 {evap_e1_cond_m3h:.1f} m³/h"];
      Boiler [label="Caldeira\\n{boiler_tph:.1f} t/h\\n{boiler_p_bara:.0f} bar(a) / {boiler_t_c:.0f} °C"];
      Turbine [label="Turbina\\n{turbine_tph:.1f} t/h\\n{turbine_mw:.1f} MW"];
      Vent [label="Atmosfera\\n{vent_tph:.1f} t/h\\n~{vent_mw:.2f} MWt", fillcolor="#FFF4E5"];
      Corn -> Fermentation;
      Fermentation -> BeerCol [label=" cerveja "];
      BeerCol -> R1 [label=" ~{r1_feed_m3h:.1f} m³/h eq. "];
      Boiler -> Turbine [label=" vapor HP "];
      Turbine -> HX [label=" vapor processo "];
      HX -> R1 [label=" calor "];
      HX -> VP [label=" condensado quente "];
      VP -> Evap [label=" vapor/flash "];
      Evap -> BeerCol [label=" vapor 3º efeito "];
      VP -> Vent [label=" excesso "];
    }}
    """
    st.graphviz_chart(dot, use_container_width=True)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("EtOH abs na Beer", f"{beer_etoh_m3h:.2f} m³/h")
    c2.metric("Tsat HX", f"{hx_tsat:.2f} °C" if IAPWS_OK else "n/a")
    c3.metric("Superaquecimento", f"{superheat:.2f} °C" if IAPWS_OK else "n/a")
    c4.metric("Perda p/ atmosfera", f"{vent_mw:.2f} MWt" if IAPWS_OK else "n/a")

with tabs[1]:
    st.subheader("Balanço de massa — núcleo etanol/água")
    df_mass = pd.DataFrame([
        ["Milho úmido", corn_tph, "t/h", status_chip("MEDIDO")],
        ["Milho seco equivalente", corn_dry_tph, "t/h", status_chip("CALCULADO")],
        ["Beer feed", beer_m3h, "m³/h", status_chip("MEDIDO")],
        ["EtOH absoluto na Beer", beer_etoh_m3h, "m³/h", status_chip("CALCULADO")],
        ["EtOH abs recuperado até R1", r1_abs_etoh_m3h, "m³/h", status_chip("CALCULADO")],
        ["R1 feed equivalente", r1_feed_m3h, "m³/h", status_chip("CALCULADO")],
        ["Água/outros no feed equivalente R1", r1_water_m3h, "m³/h", status_chip("CALCULADO")],
    ], columns=["Corrente","Valor","Unidade","Classe"])
    st.dataframe(df_mass, use_container_width=True, hide_index=True)

    c1,c2,c3 = st.columns(3)
    c1.metric("Beer / milho", f"{beer_per_corn:.3f} m³/t")
    c2.metric("EtOH abs / milho", f"{etoh_abs_l_per_tcorn:.1f} L/t")
    c3.metric("Moagem p/ 150 m³/h Beer", f"{(150/beer_per_corn if beer_per_corn else 0):.1f} t/h")
    st.warning("Ainda não é fechamento total da planta: faltam sólidos, CO₂, stillage, CDS, WDG/DDGS, óleo e perdas.")

with tabs[2]:
    st.subheader("HX-6225")
    if IAPWS_OK:
        e1,e2,e3,e4 = st.columns(4)
        e1.metric("Tsat @ P vapor", f"{hx_tsat:.2f} °C")
        e2.metric("Superaquecimento", f"{superheat:.2f} °C")
        e3.metric("Duty estimado HX", f"{hx_duty_mw:.2f} MWt")
        e4.metric("Flash teórico p/ VP", f"{flash_frac*100:.2f}%")

        q_superheat = mw_from_tph_dh(hx_steam_tph, max(0, hx_hin-hx_hg))
        q_condense = mw_from_tph_dh(hx_steam_tph, hx_hg-hx_hf)
        q_subcool = mw_from_tph_dh(hx_steam_tph, max(0, hx_hf-hx_hcond))
        energy_split = pd.DataFrame([
            ["Dessuperaquecimento", q_superheat, "MWt", status_chip("CALCULADO")],
            ["Condensação latente", q_condense, "MWt", status_chip("CALCULADO")],
            ["Sub-resfriamento condensado", q_subcool, "MWt", status_chip("CALCULADO")],
            ["Duty total estimado", hx_duty_mw, "MWt", status_chip("CALCULADO")],
        ], columns=["Parcela","Valor","Unidade","Classe"])
        st.dataframe(energy_split, use_container_width=True, hide_index=True)

        st.subheader("VP-6250 / excesso térmico")
        v1,v2,v3,v4 = st.columns(4)
        v1.metric("P sat @ T VP", f"{vp_p_bara:.3f} bar(a)")
        v2.metric("Flash teórico condensado HX", f"{flash_tph:.2f} t/h")
        v3.metric("Vapor aliviado", f"{vent_tph:.2f} t/h")
        v4.metric("Energia aliviada", f"{vent_mw:.2f} MWt")

        st.subheader("Teste da cerveja fria")
        st.write(
            f"Reduzir a cerveja de **{beer_t_c:.1f}°C para 45°C** aumenta a demanda térmica em "
            f"**{q_to_45_mw:.2f} MWt**, equivalente a **{q_to_45_tph_eq:.2f} t/h** de vapor na condição do VP-6250."
        )
        st.subheader("Turbina")
        st.write(f"Geração específica observada: **{specific_elec_kwh_per_tsteam:.1f} kWh/t de vapor**.")

with tabs[3]:
    st.subheader("Cenários operacionais")
    c1,c2 = st.columns(2)
    with c1:
        sim_corn = st.slider("Moagem [t/h]", 45.0, 65.0, float(corn_tph), 0.5)
        sim_beer_t = st.slider("T cerveja Beer Column [°C]", 35.0, 70.0, 45.0, 0.5)
        sim_hx_t = st.slider("T vapor HX-6225 [°C]", 160.0, 180.0, float(hx_t_c), 0.5)
    with c2:
        sim_cond_div_tph = st.slider("Condensado HX desviado do VP [t/h]", 0.0, min(15.0, hx_steam_tph), 0.0, 0.5)
        sim_vent_tph = st.slider("Vapor residual à atmosfera [t/h]", 0.0, 10.0, float(vent_tph), 0.1)
        sim_r1_bottom = st.slider("Base R1 [°C]", 140.0, 158.0, float(r1_bottom_c), 0.5)

    sim_beer = beer_m3h*(sim_corn/corn_tph) if corn_tph else beer_m3h
    sim_beer_mass = sim_beer*beer_rho*1000
    sim_q_beer = sim_beer_mass*beer_cp*max(0, beer_t_c-sim_beer_t)/3600/1000
    sim_beer_steam_eq = sim_q_beer*3600/vp_hfg if IAPWS_OK else float("nan")

    if IAPWS_OK:
        _, hf_simvp, _, hfg_simvp = sat_from_temp(vp6250_t_c)
        avoided_flash_frac = max(0.0, min(1.0, (hx_hcond-hf_simvp)/hfg_simvp))
        avoided_flash = sim_cond_div_tph*avoided_flash_frac
        sim_vent_mw = mw_from_tph_dh(sim_vent_tph, vp_hfg)
        sim_superheat = sim_hx_t-hx_tsat
    else:
        avoided_flash=sim_vent_mw=sim_superheat=float("nan")

    scenario = pd.DataFrame([
        ["Beer estimada", sim_beer, "m³/h"],
        ["Demanda extra por cerveja fria", sim_q_beer, "MWt"],
        ["Vapor eq. absorvido pela Beer", sim_beer_steam_eq, "t/h"],
        ["Flash evitado por desvio de condensado", avoided_flash, "t/h"],
        ["Energia residual ao vent", sim_vent_mw, "MWt"],
        ["Superaquecimento HX", sim_superheat, "°C"],
        ["Base R1", sim_r1_bottom, "°C"],
    ], columns=["Indicador","Valor","Unidade"])
    st.dataframe(scenario, use_container_width=True, hide_index=True)

    if IAPWS_OK and sim_hx_t < hx_tsat:
        st.error("Cenário coloca a temperatura abaixo de Tsat na pressão informada.")
    elif IAPWS_OK and sim_hx_t < hx_tsat+2:
        st.warning("Margem muito pequena acima de Tsat; analisar drenagem e estabilidade antes de qualquer implementação.")
    elif IAPWS_OK and sim_hx_t < hx_tsat+5:
        st.info("Vapor levemente superaquecido.")

with tabs[4]:
    st.subheader("Qualidade dos dados / fechamento")
    dq = pd.DataFrame([
        ["Moagem milho", "MEDIDO", "Confirmar calibração da balança"],
        ["Beer feed", "MEDIDO", "Bom para fechamento de volume"],
        ["Beer GL", "MEDIDO", "V3: compensar densidade/temperatura"],
        ["Vapor HX-6225", "ESTIMADO/MEDIDO", "Maior prioridade do balanço energético"],
        ["Condensado HX", "ESTIMADO", "Medição real melhora flash e duty"],
        ["Vapor ventado", "ESTIMADO", "Hoje inferido por ensaio calorimétrico"],
        ["Evap E1 condensado", "MEDIDO", "Confirmar se representa integralmente o 1º efeito"],
        ["Sólidos / stillage / coproducts", "FALTANTE", "Bloqueia fechamento integral de massa"],
    ], columns=["Variável","Classe","Comentário"])
    st.dataframe(dq, use_container_width=True, hide_index=True)

    st.subheader("Prioridade de instrumentação")
    st.write(
        "1) vapor real HX-6225; 2) vazão/temperatura condensado HX; 3) vapor/condensado por efeito; "
        "4) whole/thin stillage e CDS; 5) hidratado/anidro; 6) WDG/DDGS e umidade."
    )

with tabs[5]:
    st.subheader("Premissas e referências internas")
    st.markdown("""
- Caldeira default: 67 bar(a), 510°C, ~60 t/h.
- Turbina default: ~39 t/h, ~6 MW.
- Beer Column default: ~140 m³/h, ~18,3 GL.
- Saída Beer Column para R1: 60 GL.
- HX-6225: 5,41 barg; temperatura de vapor editável; condensado default 140°C.
- VP-6250: ~102°C.
- Base R1: referência de projeto da documentação Lucas E3 em torno de 154°C.
- Recirculação PC-6225: default 750 m³/h.
- Vapor para atmosfera: 5,4 t/h como estimativa de engenharia, não medição direta.

**Princípio da V2:** onde não há dado confiável, o app mostra a lacuna; não inventa fechamento.
    """)
    st.markdown("### Próxima V3")
    st.write(
        "Balanço por componente (água, etanol, sólidos secos, óleo, CO₂), coproducts, secadores, "
        "reconciliação de dados e tendência histórica via CSV."
    )


st.divider()
st.subheader("Exportar snapshot")
snapshot = pd.DataFrame([
    ["Moagem milho", corn_tph, "t/h"],
    ["Beer feed", beer_m3h, "m³/h"],
    ["Beer GL", beer_gl, "% v/v"],
    ["Beer temperatura", beer_t_c, "°C"],
    ["EtOH absoluto Beer", beer_etoh_m3h, "m³/h"],
    ["R1 base", r1_bottom_c, "°C"],
    ["R1 pressão", r1_pressure_barg, "barg"],
    ["R1 refluxo", r1_reflux_m3h, "m³/h"],
    ["PC-6225 recirculação", r1_recirculation_m3h, "m³/h"],
    ["HX-6225 vapor", hx_steam_tph, "t/h"],
    ["HX-6225 pressão", hx_p_barg, "barg"],
    ["HX-6225 temperatura", hx_t_c, "°C"],
    ["HX-6225 Tsat", hx_tsat if IAPWS_OK else float("nan"), "°C"],
    ["HX-6225 superaquecimento", superheat if IAPWS_OK else float("nan"), "°C"],
    ["HX-6225 duty", hx_duty_mw if IAPWS_OK else float("nan"), "MWt"],
    ["VP-6250 temperatura", vp6250_t_c, "°C"],
    ["VP-6250 nível", vp6250_level, "%"],
    ["Vapor ventado", vent_tph, "t/h"],
    ["Energia ventada", vent_mw if IAPWS_OK else float("nan"), "MWt"],
    ["Caldeira vapor", boiler_tph, "t/h"],
    ["Turbina vapor", turbine_tph, "t/h"],
    ["Turbina potência", turbine_mw, "MW"],
], columns=["Variável", "Valor", "Unidade"])

st.download_button(
    "Baixar snapshot CSV",
    data=snapshot.to_csv(index=False).encode("utf-8-sig"),
    file_name="evermat_snapshot.csv",
    mime="text/csv",
    use_container_width=True
)
