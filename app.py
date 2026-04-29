import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import colorsys

# --- 1. CONFIGURAÇÃO E LOGIN ---
st.set_page_config(page_title="Portal RH | Ploomes", layout="wide", initial_sidebar_state="collapsed")

if "logado" not in st.session_state: st.session_state.logado = False

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

# --- 2. CARGA DE DADOS ---
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

# --- 3. ESTADO E FUNÇÕES DE FILTRO ---
if "sel_area" not in st.session_state: st.session_state.sel_area = "Empresa inteira"
if "sel_nome" not in st.session_state: st.session_state.sel_nome = "Nenhum selecionado"

def mudar_colaborador():
    novo_nome = st.session_state.sb_nome
    if novo_nome != "Nenhum selecionado":
        area_destino = nome_para_area.get(novo_nome)
        if area_destino:
            st.session_state.sel_area = area_destino
            st.session_state.sel_nome = novo_nome

def mudar_area():
    st.session_state.sel_area = st.session_state.sb_area
    st.session_state.sel_nome = "Nenhum selecionado"

def escurecer_cor(hex_color, fator=0.20):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    hls = colorsys.rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    new_rgb = colorsys.hls_to_rgb(hls[0], max(0, hls[1] - fator), min(1, hls[2] + 0.1))
    return '#%02x%02x%02x' % (int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255))

# --- 4. INTERFACE ---
c1, c2, c3 = st.columns([2.5, 2.5, 0.6])
with c1:
    st.selectbox("🏢 Área de Visão:", ["Empresa inteira"] + lista_areas, 
                key="sb_area", index=(["Empresa inteira"] + lista_areas).index(st.session_state.sel_area),
                on_change=mudar_area)
with c2:
    st.selectbox("🔍 Localizar Colaborador:", ["Nenhum selecionado"] + lista_nomes, 
                key="sb_nome", index=(["Nenhum selecionado"] + lista_nomes).index(st.session_state.sel_nome),
                on_change=mudar_colaborador)
with c3:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("SAIR", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

# --- 5. TEXTOS INFORMATIVOS (RESTAURADOS) ---
# Info da Área
if st.session_state.sel_area != "Empresa inteira":
    info_area = df[df["ÁREA"] == st.session_state.sel_area]["Descricao_Area"].iloc[0]
    if info_area:
        st.info(f"**Sobre a área {st.session_state.sel_area}:** {info_area}")

# Info da Posição
if st.session_state.sel_nome != "Nenhum selecionado":
    dados_colab = df[df["NOME"] == st.session_state.sel_nome].iloc[0]
    if "Info_Posicao" in df.columns and dados_colab["Info_Posicao"]:
        st.success(f"**Posição de {st.session_state.sel_nome}:** {dados_colab['Info_Posicao']}")

# --- 6. GRÁFICO ---
palette = ["#FF00FF","#00FFFF","#FFFF00","#FF4500","#32CD32","#7B68EE","#FF1493","#A9A9A9","#ADFF2F","#FFD700"]
area_color = {a: palette[i % len(palette)] for i, a in enumerate(lista_areas)}

if st.session_state.sel_area == "Empresa inteira":
    df_view = df
else:
    df_view = df[df["ÁREA"] == st.session_state.sel_area]
    lideres_nomes = df_view["LIDER DIRETO"].unique()
    df_view = pd.concat([df_view, df[df["NOME"].isin(lideres_nomes)]]).drop_duplicates(subset=["NOME"])

nodes = []
for _, row in df_view.iterrows():
    n = row["NOME"]
    cor_b = area_color.get(row["ÁREA"], "#7443F6")
    cor_f = "#000000"
    if n == st.session_state.sel_nome: cor_b, cor_f = "#2B7CE9", "#FFFFFF"

    nodes.append({
        "id": n, "label": f"<b>{n}</b>\n{row['CARGO']}",
        "color": {"background": cor_b, "border": escurecer_cor(cor_b)},
        "font": {"multi": "html", "color": cor_f, "face": "Arial", "size": 25},
        "shape": "box", "margin": 15, "widthConstraint": {"maximum": 200}
    })

edges = [{"from": r["LIDER DIRETO"], "to": r["NOME"], "arrows": "to", "color": "#AAAAAA"} 
         for _, r in df_view.iterrows() if r["LIDER DIRETO"] in df_view["NOME"].values]

html_vis = f"""
<div id="mynetwork" style="height: 750px; border: 1px solid #ddd; border-radius: 10px;"></div>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<script>
    var container = document.getElementById('mynetwork');
    var data = {{ nodes: new vis.DataSet({json.dumps(nodes)}), edges: new vis.DataSet({json.dumps(edges)}) }};
    var options = {{
        physics: {{
            enabled: true,
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {{
                gravitationalConstant: -200, // Ajustado para evitar sobreposição (cards um em cima do outro)
                springLength: 200,
                springConstant: 0.05,
                avoidOverlap: 1 // Força os cards a se repelirem
            }},
            stabilization: {{ iterations: 100 }}
        }},
        interaction: {{ hover: true, dragNodes: true }}
    }};
    var network = new vis.Network(container, data, options);
    
    network.once('stabilized', function() {{
        var search = "{st.session_state.sel_nome}";
        if(search !== "Nenhum selecionado") {{
            network.focus(search, {{ scale: 0.7, animation: true }});
        }}
    }});
</script>
"""
components.html(html_vis, height=770)
