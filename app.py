import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import colorsys
import unicodedata

# Configuração inicial deve ser a primeira instrução
st.set_page_config(page_title="Portal RH | Ploomes", layout="wide", initial_sidebar_state="collapsed")

# --- HELPERS OTIMIZADOS ---
def _normalizar_nome(texto):
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).upper().strip()

@st.cache_data
def _resolver_lider(lider, lista_nomes_set):
    if not lider or lider in lista_nomes_set:
        return lider
    # Lógica de busca aproximada simplificada para performance
    return lider 

def escurecer_cor(hex_color, fator=0.15):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    hls = colorsys.rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    new_rgb = colorsys.hls_to_rgb(hls[0], max(0, hls[1] - fator), min(1, hls[2] + 0.1))
    return '#%02x%02x%02x' % (int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255))

# --- CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');
html, body, [class*="st-"] { font-family: 'Manrope', sans-serif; }
header { visibility: hidden !important; }
.block-container { padding-top: 1rem !important; }
.info-box {
    background: #fcfcfc; border-radius: 15px; padding: 15px;
    border-left: 6px solid #7443F6; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 10px;
}
.info-label { color: #7443F6; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; }
.info-text  { color: #444; font-size: 0.9rem; }
.legend-container {
    background: #fff; border-radius: 15px; padding: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #eee;
}
.legend-item { display: flex; align-items: center; margin-bottom: 6px; font-size: 0.75rem; font-weight: 600; }
.legend-color { width: 16px; height: 16px; border-radius: 4px; margin-right: 8px; flex-shrink: 0; }
</style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.title("Ploomes")
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            if u == "RHPloomes" and s == "RHPloomes":
                st.session_state.logado = True
                st.rerun()
    st.stop()

# --- CARGA DE DADOS (CACHE ESTRITO) ---
@st.cache_data(ttl=3600)
def get_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTLRqVZ9LWZMaPQ9MFGvOcQ8i-_ljOeKPO8w1jpwTscup0VM1ERFYgwitfmH0Zjfo-u9-fjfd60goF1/pub?output=csv"
    df = pd.read_csv(url).fillna("")
    df.columns = df.columns.str.strip()
    df["ÁREA"] = df["ÁREA"].str.upper()
    return df

df = get_data()

# --- INICIALIZAÇÃO DO ESTADO ---
if "sel_area" not in st.session_state:
    st.session_state.sel_area = "Empresa inteira"
if "sel_nome" not in st.session_state:
    st.session_state.sel_nome = "Nenhum selecionado"

# Mapeamentos para busca rápida
lista_nomes = sorted(df["NOME"].unique().tolist())
lista_areas = sorted(df["ÁREA"].unique().tolist())
nome_para_area = dict(zip(df["NOME"], df["ÁREA"]))

# --- CALLBACKS (Sincronização Automática) ---
def mudar_area():
    st.session_state.sel_area = st.session_state.sb_area
    st.session_state.sel_nome = "Nenhum selecionado"

def mudar_nome():
    nome = st.session_state.sb_nome
    st.session_state.sel_nome = nome
    if nome != "Nenhum selecionado":
        area_do_colaborador = nome_para_area.get(nome)
        if area_do_colaborador:
            st.session_state.sel_area = area_do_colaborador

# --- INTERFACE DE FILTROS ---
c1, c2, c3 = st.columns([2, 2, 0.5])

with c1:
    st.selectbox("🏢 Área de Visão:", ["Empresa inteira"] + lista_areas, 
                 key="sb_area", 
                 index=(["Empresa inteira"] + lista_areas).index(st.session_state.sel_area),
                 on_change=mudar_area)

with c2:
    st.selectbox("🔍 Localizar Colaborador:", ["Nenhum selecionado"] + lista_nomes, 
                 key="sb_nome",
                 index=(["Nenhum selecionado"] + lista_nomes).index(st.session_state.sel_nome),
                 on_change=mudar_nome)

with c3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("SAIR"):
        st.session_state.logado = False
        st.rerun()

# --- PROCESSAMENTO DO ORGANOGRAMA ---
area_sel = st.session_state.sel_area
busca_nome = st.session_state.sel_nome

# Info Boxes
if busca_nome != "Nenhum selecionado":
    row = df[df["NOME"] == busca_nome].iloc[0]
    i1, i2 = st.columns(2)
    with i1:
        st.markdown(f'<div class="info-box"><div class="info-label">ÁREA</div><div class="info-text">{row["Descricao_Area"]}</div></div>', unsafe_allow_html=True)
    with i2:
        st.markdown(f'<div class="info-box"><div class="info-label">POSIÇÃO</div><div class="info-text">{row["Info_Posicao"]}</div></div>', unsafe_allow_html=True)

# Filtro de visualização
if area_sel == "Empresa inteira":
    df_view = df
else:
    df_view = df[df["ÁREA"] == area_sel]
    # Inclui líderes para não quebrar a árvore
    lideres = df_view["LIDER DIRETO"].unique()
    df_lideres = df[df["NOME"].isin(lideres)]
    df_view = pd.concat([df_view, df_lideres]).drop_duplicates(subset=["NOME"])

# Cores
palette = ["#FF00FF","#00FFFF","#FFFF00","#FF4500","#32CD32","#7B68EE","#FF1493","#A9A9A9"]
unique_areas = sorted(df["ÁREA"].unique())
area_color = {a: palette[i % len(palette)] for i, a in enumerate(unique_areas)}

# --- CONSTRUÇÃO DO COMPONENTE VIS-NETWORK ---
nodes = []
for _, row in df_view.iterrows():
    cor_base = area_color.get(row["ÁREA"], "#7443F6")
    cor_borda = escurecer_cor(cor_base)
    cor_fonte = "#000000"
    
    if row["NOME"] == busca_nome:
        cor_base, cor_fonte, cor_borda = "#000000", "#FFFFFF", "#000000"

    nodes.append({
        "id": row["NOME"],
        "label": f"<b>{row['NOME']}</b>\n{row['CARGO']}",
        "color": {"background": cor_base, "border": cor_borda},
        "font": {"multi": "html", "color": cor_fonte, "size": 20},
        "shape": "box",
        "margin": 10
    })

edges = [{"from": r["LIDER DIRETO"], "to": r["NOME"], "arrows": "to"} 
         for _, r in df_view.iterrows() if r["LIDER DIRETO"] in df_view["NOME"].values]

html_vis = f"""
<div id="mynetwork" style="height: 600px; background: #ffffff; border-radius: 20px;"></div>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<script>
    var nodes = new vis.DataSet({json.dumps(nodes)});
    var edges = new vis.DataSet({json.dumps(edges)});
    var container = document.getElementById('mynetwork');
    var data = {{ nodes: nodes, edges: edges }};
    var options = {{
        physics: {{
            stabilization: {{ iterations: 50 }},
            forceAtlas2Based: {{ gravitationalConstant: -100, springLength: 100 }},
            solver: 'forceAtlas2Based'
        }},
        layout: {{ hierarchical: {{ enabled: true, direction: 'UD', sortMethod: 'directed', nodeSpacing: 200 }} }}
    }};
    var network = new vis.Network(container, data, options);
    
    // Focar no selecionado imediatamente
    var search = "{busca_nome}";
    if(search !== "Nenhum selecionado") {{
        network.once('stabilized', function() {{
            network.focus(search, {{ scale: 0.8, animation: true }});
        }});
    }}
</script>
"""

col_leg, col_org = st.columns([1, 4])
with col_leg:
    for area, color in area_color.items():
        st.markdown(f'<div class="legend-item"><div class="legend-color" style="background:{color}"></div>{area}</div>', unsafe_allow_html=True)

with col_org:
    components.html(html_vis, height=650)
