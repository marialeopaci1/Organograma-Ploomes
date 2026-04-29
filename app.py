import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import colorsys
import unicodedata

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Portal RH | Ploomes", layout="wide", initial_sidebar_state="collapsed")

# Inicialização do estado
if "sel_area" not in st.session_state: st.session_state.sel_area = "Empresa inteira"
if "sel_nome" not in st.session_state: st.session_state.sel_nome = "Nenhum selecionado"
if "logado" not in st.session_state: st.session_state.logado = False

# --- 2. FUNÇÕES DE SUPORTE ---
def _normalizar(texto):
    if not texto: return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).upper().strip()

def escurecer_cor(hex_color, fator=0.20):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    hls = colorsys.rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    new_rgb = colorsys.hls_to_rgb(hls[0], max(0, hls[1] - fator), min(1, hls[2] + 0.1))
    return '#%02x%02x%02x' % (int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255))

# --- 3. CARGA DE DADOS ---
@st.cache_data(ttl=3600)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTLRqVZ9LWZMaPQ9MFGvOcQ8i-_ljOeKPO8w1jpwTscup0VM1ERFYgwitfmH0Zjfo-u9-fjfd60goF1/pub?output=csv"
    df = pd.read_csv(url).fillna("")
    df.columns = df.columns.str.strip()
    df["ÁREA"] = df["ÁREA"].str.upper().str.strip()
    return df

df = carregar_dados()
lista_nomes = sorted(df["NOME"].unique().tolist())
lista_areas = sorted(df["ÁREA"].unique().tolist())
nome_para_area = dict(zip(df["NOME"], df["ÁREA"]))

# --- 4. LÓGICA DE FILTRO AUTOMÁTICO (O CORAÇÃO DO AJUSTE) ---
def mudar_colaborador():
    novo_nome = st.session_state.sb_nome
    if novo_nome != "Nenhum selecionado":
        area_destino = nome_para_area.get(novo_nome)
        if area_destino:
            st.session_state.sel_area = area_destino
            st.session_state.sel_nome = novo_nome
    else:
        st.session_state.sel_nome = "Nenhum selecionado"

def mudar_area():
    st.session_state.sel_area = st.session_state.sb_area
    # Se mudar a área manualmente, resetamos a busca por nome para evitar conflitos
    st.session_state.sel_nome = "Nenhum selecionado"

# --- 5. INTERFACE SUPERIOR ---
if st.session_state.logado:
    c1, c2, c3 = st.columns([2.5, 2.5, 0.6])
    with c1:
        st.selectbox("🏢 Área de Visão:", ["Empresa inteira"] + lista_areas, 
                    key="sb_area", 
                    index=(["Empresa inteira"] + lista_areas).index(st.session_state.sel_area),
                    on_change=mudar_area)
    with c2:
        st.selectbox("🔍 Localizar Colaborador:", ["Nenhum selecionado"] + lista_nomes, 
                    key="sb_nome", 
                    index=(["Nenhum selecionado"] + lista_nomes).index(st.session_state.sel_nome),
                    on_change=mudar_colaborador)
    with c3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("SAIR", use_container_width=True):
            st.session_state.logado = False
            st.rerun()

# --- 6. PROCESSAMENTO E CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');
html, body, [class*="st-"] { font-family: 'Manrope', sans-serif; }
.legend-sidebar { background: white; border-radius: 12px; padding: 12px; border: 1px solid #eee; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.legend-item { display: flex; align-items: center; margin-bottom: 8px; font-size: 0.8rem; font-weight: 600; }
.legend-color { width: 16px; height: 16px; border-radius: 4px; margin-right: 10px; }
</style>
""", unsafe_allow_html=True)

if not st.session_state.logado:
    # (Código de login omitido aqui para brevidade, manter o mesmo do anterior)
    if st.button("ACESSAR"): st.session_state.logado = True; st.rerun()
    st.stop()

# --- 7. RENDERIZAÇÃO DO GRÁFICO ---
col_side, col_main = st.columns([0.8, 5])

with col_side:
    palette = ["#FF00FF","#00FFFF","#FFFF00","#FF4500","#32CD32","#7B68EE","#FF1493","#A9A9A9","#ADFF2F","#FFD700"]
    area_color = {a: palette[i % len(palette)] for i, a in enumerate(lista_areas)}
    st.markdown('<div class="legend-sidebar">', unsafe_allow_html=True)
    st.markdown('<div class="legend-item"><div class="legend-color" style="background:#2B7CE9"></div>SELECIONADO</div>', unsafe_allow_html=True)
    for area, color in area_color.items():
        st.markdown(f'<div class="legend-item"><div class="legend-color" style="background:{color}"></div>{area}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    # Filtro de dados rigoroso
    if st.session_state.sel_area == "Empresa inteira":
        df_view = df
    else:
        df_view = df[df["ÁREA"] == st.session_state.sel_area]
        # Adiciona líderes que podem estar fora da área para manter a estrutura
        lideres_nomes = df_view["LIDER DIRETO"].unique()
        df_view = pd.concat([df_view, df[df["NOME"].isin(lideres_nomes)]]).drop_duplicates(subset=["NOME"])

    nodes = []
    for _, row in df_view.iterrows():
        n = row["NOME"]
        cor_b = area_color.get(row["ÁREA"], "#7443F6")
        cor_f = "#000000"
        
        # Destaque para o selecionado
        if n == st.session_state.sel_nome:
            cor_b, cor_f = "#2B7CE9", "#FFFFFF"

        nodes.append({
            "id": n, "label": f"<b>{n}</b>\n{row['CARGO']}",
            "color": {"background": cor_b, "border": escurecer_cor(cor_b)},
            "font": {"multi": "html", "color": cor_f, "face": "Manrope"},
            "shape": "box", "margin": 20
        })

    edges = [{"from": r["LIDER DIRETO"], "to": r["NOME"], "arrows": "to"} 
             for _, r in df_view.iterrows() if r["LIDER DIRETO"] in df_view["NOME"].values]

    html_vis = f"""
    <div id="mynetwork" style="height: 800px;"></div>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script>
        var container = document.getElementById('mynetwork');
        var data = {{ nodes: new vis.DataSet({json.dumps(nodes)}), edges: new vis.DataSet({json.dumps(edges)}) }};
        var options = {{
            physics: {{ enabled: true, solver: 'forceAtlas2Based', stabilization: {{ iterations: 150 }} }},
            interaction: {{ hover: true }}
        }};
        var network = new vis.Network(container, data, options);
        
        // Foca no colaborador selecionado após carregar
        network.once('stabilized', function() {{
            var search = "{st.session_state.sel_nome}";
            if(search !== "Nenhum selecionado") {{
                network.focus(search, {{ scale: 0.5, animation: true }});
            }}
        }});
    </script>
    """
    components.html(html_vis, height=820)
