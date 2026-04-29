import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import colorsys
import unicodedata

# Configuração de página
st.set_page_config(page_title="Portal RH | Ploomes", layout="wide", initial_sidebar_state="collapsed")

# --- FUNÇÕES DE SUPORTE ---
def _normalizar_nome(texto):
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).upper().strip()

def escurecer_cor(hex_color, fator=0.15):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    hls = colorsys.rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    new_rgb = colorsys.hls_to_rgb(hls[0], max(0, hls[1] - fator), min(1, hls[2] + 0.1))
    return '#%02x%02x%02x' % (int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255))

# --- ESTILIZAÇÃO CSS ---
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
.info-label { color: #7443F6; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; margin-bottom: 5px; }
.info-text  { color: #444; font-size: 0.93rem; line-height: 1.4; }
.legend-container {
    background: #fff; border-radius: 15px; padding: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #eee;
}
.legend-item { display: flex; align-items: center; margin-bottom: 8px; font-size: 0.8rem; font-weight: 600; }
.legend-color { width: 18px; height: 18px; border-radius: 5px; margin-right: 10px; flex-shrink: 0; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

# --- SISTEMA DE LOGIN ---
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div style="text-align:center; padding: 40px; background: white; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1)">', unsafe_allow_html=True)
        st.title("Ploomes")
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            if u == "RHPloomes" and s == "RHPloomes":
                st.session_state.logado = True
                st.rerun()
    st.stop()

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=3600)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTLRqVZ9LWZMaPQ9MFGvOcQ8i-_ljOeKPO8w1jpwTscup0VM1ERFYgwitfmH0Zjfo-u9-fjfd60goF1/pub?output=csv"
    df = pd.read_csv(url).fillna("")
    df.columns = df.columns.str.strip()
    df["ÁREA"] = df["ÁREA"].str.upper().str.strip()
    return df

df = carregar_dados()

# Mapeamentos para performance
lista_nomes = sorted(df["NOME"].unique().tolist())
lista_areas = sorted(df["ÁREA"].unique().tolist())
nome_para_area = dict(zip(df["NOME"], df["ÁREA"]))

# --- ESTADO DOS FILTROS ---
if "sel_area" not in st.session_state:
    st.session_state.sel_area = "Empresa inteira"
if "sel_nome" not in st.session_state:
    st.session_state.sel_nome = "Nenhum selecionado"

# --- CALLBACKS ---
def ao_mudar_area():
    st.session_state.sel_area = st.session_state.sb_area
    st.session_state.sel_nome = "Nenhum selecionado"

def ao_mudar_nome():
    nome = st.session_state.sb_nome
    st.session_state.sel_nome = nome
    if nome != "Nenhum selecionado":
        area_colab = nome_para_area.get(nome)
        if area_colab:
            st.session_state.sel_area = area_colab

# --- INTERFACE ---
c1, c2, c3 = st.columns([2.5, 2.5, 0.6])

with c1:
    st.selectbox("🏢 Área de Visão:", ["Empresa inteira"] + lista_areas, 
                 key="sb_area", 
                 index=(["Empresa inteira"] + lista_areas).index(st.session_state.sel_area),
                 on_change=ao_mudar_area)

with c2:
    st.selectbox("🔍 Localizar Colaborador:", ["Nenhum selecionado"] + lista_nomes, 
                 key="sb_nome",
                 index=(["Nenhum selecionado"] + lista_nomes).index(st.session_state.sel_nome),
                 on_change=ao_mudar_nome)

with c3:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("SAIR", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

# --- LÓGICA DE FILTRAGEM ---
area_sel = st.session_state.sel_area
busca_nome = st.session_state.sel_nome

if busca_nome != "Nenhum selecionado":
    row = df[df["NOME"] == busca_nome].iloc[0]
    i1, i2 = st.columns(2)
    with i1:
        st.markdown(f'<div class="info-box"><div class="info-label">DESCRIÇÃO DA ÁREA: {row["ÁREA"]}</div><div class="info-text">{row["Descricao_Area"]}</div></div>', unsafe_allow_html=True)
    with i2:
        st.markdown(f'<div class="info-box"><div class="info-label">INFO DA POSIÇÃO: {row["CARGO"]}</div><div class="info-text">{row["Info_Posicao"]}</div></div>', unsafe_allow_html=True)

if area_sel == "Empresa inteira":
    df_view = df
else:
    df_area = df[df["ÁREA"] == area_sel]
    lideres = df_area["LIDER DIRETO"].unique()
    df_lideres = df[df["NOME"].isin(lideres)]
    df_view = pd.concat([df_area, df_lideres]).drop_duplicates(subset=["NOME"])

# --- CORES ---
palette = ["#FF00FF","#00FFFF","#FFFF00","#FF4500","#32CD32","#7B68EE","#FF1493","#A9A9A9","#ADFF2F","#FFD700"]
area_color = {a: palette[i % len(palette)] for i, a in enumerate(lista_areas)}

# --- NÓS E ARESTAS ---
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
        "font": {"multi": "html", "color": cor_fonte, "size": 18, "face": "Manrope"},
        "shape": "box",
        "margin": 10,
        "shadow": True
    })

edges = [{"from": r["LIDER DIRETO"], "to": r["NOME"], "arrows": "to", "color": "#888888"} 
         for _, r in df_view.iterrows() if r["LIDER DIRETO"] in df_view["NOME"].values]

# --- HTML/JS (FÍSICA ORIGINAL MELHORADA) ---
html_vis = f"""
<div id="mynetwork" style="height: 800px; background: #ffffff;"></div>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<script>
    var nodes = new vis.DataSet({json.dumps(nodes)});
    var edges = new vis.DataSet({json.dumps(edges)});
    var container = document.getElementById('mynetwork');
    var data = {{ nodes: nodes, edges: edges }};
    
    var options = {{
        physics: {{
            enabled: true,
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {{
                gravitationalConstant: -100, // Força de repulsão para não embolar
                centralGravity: 0.005,       // Puxa levemente para o centro
                springLength: 200,          // Tamanho das "molas" entre líder e liderado
                springConstant: 0.08,
                avoidOverlap: 1             // CRÍTICO: Impede um nó de ficar em cima do outro
            }},
            stabilization: {{
                enabled: true,
                iterations: 100,            // Pré-calcula a posição antes de mostrar
                updateInterval: 25
            }}
        }},
        interaction: {{ dragNodes: true, zoomView: true, dragView: true }}
    }};
    
    var network = new vis.Network(container, data, options);

    // Quando terminar de "flutuar" e parar, desligamos a física para economizar CPU
    network.on("stabilizationIterationsDone", function () {{
        network.setOptions({{ physics: false }});
    }});

    var search = "{busca_nome}";
    if(search !== "Nenhum selecionado") {{
        network.focus(search, {{ scale: 0.9, animation: true }});
        network.selectNodes([search]);
    }} else {{
        network.fit();
    }}
</script>
"""

col_leg, col_org = st.columns([1, 4.5])
with col_leg:
    st.markdown('<div class="legend-container">', unsafe_allow_html=True)
    st.markdown('<div style="font-weight:900; margin-bottom:15px; font-size:0.85rem;">LEGENDA</div>', unsafe_allow_html=True)
    st.markdown('<div class="legend-item"><div class="legend-color" style="background:#000000"></div>SELECIONADO</div>', unsafe_allow_html=True)
    st.markdown('<hr style="border:0.5px solid #eee; margin:10px 0;">', unsafe_allow_html=True)
    for area, color in area_color.items():
        st.markdown(f'<div class="legend-item"><div class="legend-color" style="background:{color}"></div>{area}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_org:
    components.html(html_vis, height=820)
