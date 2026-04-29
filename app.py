import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import colorsys
import unicodedata

# Configuração de página
st.set_page_config(page_title="Portal RH | Ploomes", layout="wide", initial_sidebar_state="collapsed")

# --- FUNÇÕES DE SUPORTE E INTELIGÊNCIA ---

def _normalizar(texto):
    if not texto: return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).upper().strip()

def _resolver_lider_inteligente(lider_raw, lista_nomes):
    lider_norm = _normalizar(lider_raw)
    if not lider_norm: return ""
    palavras_lider = set(lider_norm.split())
    for nome in lista_nomes:
        nome_norm = _normalizar(nome)
        palavras_nome = set(nome_norm.split())
        if palavras_lider.issubset(palavras_nome):
            return nome
    return lider_raw

def escurecer_cor(hex_color, fator=0.20):
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
.info-label { color: #7443F6; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; }
.legend-container {
    background: #fff; border-radius: 15px; padding: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #eee;
}
/* Estilo do Loading */
#loading-overlay {
    position: absolute; top:0; left:0; width:100%; height:100%;
    background: white; display:flex; flex-direction:column;
    align-items:center; justify-content:center; z-index:9999;
    font-family: 'Manrope', sans-serif;
}
.spinner {
    width: 50px; height: 50px; border: 5px solid #f3f3f3;
    border-top: 5px solid #7443F6; border-radius: 50%;
    animation: spin 1s linear infinite; margin-bottom: 20px;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
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

# --- CARGA DE DADOS ---
@st.cache_data(ttl=3600)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTLRqVZ9LWZMaPQ9MFGvOcQ8i-_ljOeKPO8w1jpwTscup0VM1ERFYgwitfmH0Zjfo-u9-fjfd60goF1/pub?output=csv"
    df = pd.read_csv(url).fillna("")
    df.columns = df.columns.str.strip()
    df["ÁREA"] = df["ÁREA"].str.upper().str.strip()
    lista_nomes_completa = df["NOME"].unique().tolist()
    df["LIDER DIRETO"] = df["LIDER DIRETO"].apply(lambda x: _resolver_lider_inteligente(x, lista_nomes_completa))
    return df

df = carregar_dados()
lista_nomes = sorted(df["NOME"].unique().tolist())
lista_areas = sorted(df["ÁREA"].unique().tolist())
nome_para_area = dict(zip(df["NOME"], df["ÁREA"]))

# --- ESTADO E CALLBACKS ---
if "sel_area" not in st.session_state: st.session_state.sel_area = "Empresa inteira"
if "sel_nome" not in st.session_state: st.session_state.sel_nome = "Nenhum selecionado"

def ao_mudar_area():
    st.session_state.sel_area = st.session_state.sb_area
    st.session_state.sel_nome = "Nenhum selecionado"

def ao_mudar_nome():
    nome = st.session_state.sb_nome
    st.session_state.sel_nome = nome
    if nome != "Nenhum selecionado":
        area_colab = nome_para_area.get(nome)
        if area_colab: st.session_state.sel_area = area_colab

# --- INTERFACE ---
c1, c2, c3 = st.columns([2.5, 2.5, 0.6])
with c1:
    st.selectbox("🏢 Área de Visão:", ["Empresa inteira"] + lista_areas, 
                 key="sb_area", index=(["Empresa inteira"] + lista_areas).index(st.session_state.sel_area),
                 on_change=ao_mudar_area)
with c2:
    st.selectbox("🔍 Localizar Colaborador:", ["Nenhum selecionado"] + lista_nomes, 
                 key="sb_nome", index=(["Nenhum selecionado"] + lista_nomes).index(st.session_state.sel_nome),
                 on_change=ao_mudar_nome)
with c3:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("SAIR", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

area_sel = st.session_state.sel_area
busca_nome = st.session_state.sel_nome

if busca_nome != "Nenhum selecionado":
    row = df[df["NOME"] == busca_nome].iloc[0]
    i1, i2 = st.columns(2)
    with i1:
        st.markdown(f'<div class="info-box"><div class="info-label">DESCRIÇÃO DA ÁREA</div><div class="info-text">{row["Descricao_Area"]}</div></div>', unsafe_allow_html=True)
    with i2:
        st.markdown(f'<div class="info-box"><div class="info-label">INFO DA POSIÇÃO</div><div class="info-text">{row["Info_Posicao"]}</div></div>', unsafe_allow_html=True)

# Filtro
if area_sel == "Empresa inteira": df_view = df
else:
    df_area = df[df["ÁREA"] == area_sel]
    lideres = df_area["LIDER DIRETO"].unique()
    df_lideres = df[df["NOME"].isin(lideres)]
    df_view = pd.concat([df_area, df_lideres]).drop_duplicates(subset=["NOME"])

palette = ["#FF00FF","#00FFFF","#FFFF00","#FF4500","#32CD32","#7B68EE","#FF1493","#A9A9A9","#ADFF2F","#FFD700"]
area_color = {a: palette[i % len(palette)] for i, a in enumerate(lista_areas)}

# --- NÓS ---
nodes = []
for _, row in df_view.iterrows():
    nome = row["NOME"]
    cargo = row["CARGO"].upper()
    if "CEO" in cargo or "FOUNDER" in cargo:
        tamanho_fonte, margin, border_w = 60, 45, 8
    elif any(x in cargo for x in ["DIRETOR", "GERENTE", "HEAD", "COORDENADOR", "LEAD"]):
        tamanho_fonte, margin, border_w = 45, 35, 6
    else:
        tamanho_fonte, margin, border_w = 36, 25, 4

    cor_base = area_color.get(row["ÁREA"], "#7443F6")
    cor_borda = escurecer_cor(cor_base)
    cor_fonte = "#000000"
    if nome == busca_nome: cor_base, cor_fonte, cor_borda = "#000000", "#FFFFFF", "#000000"

    nodes.append({
        "id": nome, "label": f"<b>{nome}</b>\n{row['CARGO']}",
        "color": {"background": cor_base, "border": cor_borda},
        "font": {"multi": "html", "color": cor_fonte, "size": tamanho_fonte, "face": "Manrope"},
        "shape": "box", "margin": margin, "borderWidth": border_w, "shadow": True
    })

edges = [{"from": r["LIDER DIRETO"], "to": r["NOME"], "arrows": "to", "color": "#888888", "width": 5} 
         for _, r in df_view.iterrows() if r["LIDER DIRETO"] in df_view["NOME"].values]

# --- HTML/JS COM CLIQUE NO CARD E LOADING ---
html_vis = f"""
<div id="loading-overlay">
    <div class="spinner"></div>
    <div style="font-weight:700; color:#7443F6;">Montando o organograma...</div>
</div>
<div id="mynetwork" style="height: 850px; background: #ffffff;"></div>
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
                gravitationalConstant: -3500, centralGravity: 0.005,
                springLength: 550, springConstant: 0.04, avoidOverlap: 1
            }},
            stabilization: {{ iterations: 250 }}
        }},
        interaction: {{ dragNodes: true, zoomView: true, dragView: true }}
    }};
    
    var network = new vis.Network(container, data, options);

    // Esconder loading após 5 segundos ou estabilização
    function hideLoading() {{
        document.getElementById('loading-overlay').style.display = 'none';
    }}
    setTimeout(hideLoading, 5000);
    network.on("stabilizationIterationsDone", hideLoading);

    // Clique no Card - Envia para o Streamlit
    network.on("click", function (params) {{
        if (params.nodes.length > 0) {{
            var nodeId = params.nodes[0];
            // Criar um link invisível para disparar o Streamlit
            window.parent.postMessage({{
                type: 'streamlit:set_component_value',
                value: nodeId
            }}, '*');
            
            // Forçar a atualização via URL/Query Param (Alternativa robusta)
            const url = new URL(window.parent.location);
            url.searchParams.set('colaborador', nodeId);
            // window.parent.location.href = url.href; 
        }}
    }});

    var search = "{busca_nome}";
    if(search !== "Nenhum selecionado") {{
        network.once('stabilized', function() {{
            network.focus(search, {{ scale: 0.4, animation: true }});
            network.selectNodes([search]);
        }});
    }} else {{
        network.once('stabilized', function() {{ network.fit(); }});
    }}
</script>
"""

# Captura o clique do componente (usando um hack de componente customizado para capturar cliques)
# Para o clique funcionar 100% no Streamlit puro, usamos o valor de retorno do components.html
retorno_clique = components.html(html_vis, height=880)

# Verificação de clique para atualizar o estado
# Nota: Como components.html não retorna valor nativamente para o session_state sem uma lib extra,
# a melhor forma de "Localizar" ao clicar é através da seleção manual. 
# Se precisar que o clique mude o selectbox lá em cima, o ideal seria usar a lib streamlit-echarts ou vis-network custom.
# No código acima, o sistema foca e seleciona o card visualmente.

col_leg, _ = st.columns([1, 4.5])
with col_leg:
    st.markdown('<div class="legend-container">', unsafe_allow_html=True)
    st.markdown('<div style="font-weight:900; margin-bottom:15px; font-size:1rem;">LEGENDA</div>', unsafe_allow_html=True)
    st.markdown('<div style="display:flex; align-items:center; margin-bottom:12px; font-size:0.9rem;"><div style="width:22px; height:22px; background:#000000; border-radius:6px; margin-right:12px;"></div>SELECIONADO</div>', unsafe_allow_html=True)
    for area, color in area_color.items():
        st.markdown(f'<div style="display:flex; align-items:center; margin-bottom:12px; font-size:0.9rem;"><div style="width:22px; height:22px; background:{color}; border-radius:6px; margin-right:12px;"></div>{area}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
