import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import colorsys
import unicodedata

# --- 1. CONFIGURAÇÃO E SINCRONIZAÇÃO ---
st.set_page_config(page_title="Portal RH | Ploomes", layout="wide", initial_sidebar_state="collapsed")

# Inicialização segura do estado
if "sel_area" not in st.session_state: st.session_state.sel_area = "Empresa inteira"
if "sel_nome" not in st.session_state: st.session_state.sel_nome = "Nenhum selecionado"
if "logado" not in st.session_state: st.session_state.logado = False

# Captura clique vindo do gráfico (via URL)
if "colab" in st.query_params:
    st.session_state.sel_nome = st.query_params["colab"]

# --- 2. FUNÇÕES DE SUPORTE ---
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

# --- 3. CARGA DE DADOS ---
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
# Dicionário para busca rápida de área por nome
nome_para_area = dict(zip(df["NOME"], df["ÁREA"]))

# --- LÓGICA DE FILTRO AUTOMÁTICO (O QUE VOCÊ PEDIU) ---
# Se um colaborador foi localizado, forçamos a área de visão a ser a dele
if st.session_state.sel_nome != "Nenhum selecionado":
    area_do_colaborador = nome_para_area.get(st.session_state.sel_nome)
    if area_do_colaborador:
        st.session_state.sel_area = area_do_colaborador

# --- 4. CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');
html, body, [class*="st-"] { font-family: 'Manrope', sans-serif; }
header { visibility: hidden !important; }
.block-container { padding-top: 1rem !important; }

.legend-sidebar {
    background: #ffffff; border-radius: 12px; padding: 12px; border: 1px solid #eee;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05); max-height: 75vh; overflow-y: auto;
}
.legend-title { font-weight: 800; font-size: 0.75rem; color: #999; text-transform: uppercase; margin-bottom: 10px; }
.legend-item { display: flex; align-items: center; margin-bottom: 8px; font-size: 0.8rem; font-weight: 600; }
.legend-color { width: 16px; height: 16px; border-radius: 4px; margin-right: 10px; flex-shrink: 0; }

#loading-overlay {
    position: absolute; top:0; left:0; width:100%; height:100%;
    background: white; display:flex; flex-direction:column;
    align-items:center; justify-content:center; z-index:9999;
}
.spinner {
    width: 60px; height: 60px; border: 6px solid #f3f3f3;
    border-top: 6px solid #7443F6; border-radius: 50%;
    animation: spin 1s linear infinite; margin-bottom: 20px;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
""", unsafe_allow_html=True)

# --- 5. LOGIN ---
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

# --- 6. INTERFACE SUPERIOR ---
c1, c2, c3 = st.columns([2.5, 2.5, 0.6])
with c1:
    area_sel = st.selectbox("🏢 Área de Visão:", ["Empresa inteira"] + lista_areas, 
                            key="sb_area", 
                            index=(["Empresa inteira"] + lista_areas).index(st.session_state.sel_area))
    st.session_state.sel_area = area_sel
with c2:
    # Se a área mudou manualmente, poderíamos resetar o nome, mas manter é melhor para navegação
    busca_nome = st.selectbox("🔍 Localizar Colaborador:", ["Nenhum selecionado"] + lista_nomes, 
                              key="sb_nome", 
                              index=(["Nenhum selecionado"] + lista_nomes).index(st.session_state.sel_nome))
    st.session_state.sel_nome = busca_nome
with c3:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("SAIR", use_container_width=True):
        st.session_state.logado = False
        st.query_params.clear()
        st.rerun()

# --- 7. ORGANOGRAMA ---
col_side, col_main = st.columns([0.8, 5])

with col_side:
    palette = ["#FF00FF","#00FFFF","#FFFF00","#FF4500","#32CD32","#7B68EE","#FF1493","#A9A9A9","#ADFF2F","#FFD700"]
    area_color = {a: palette[i % len(palette)] for i, a in enumerate(lista_areas)}
    st.markdown('<div class="legend-sidebar"><div class="legend-title">Legenda</div>', unsafe_allow_html=True)
    # Legenda corrigida: Azul para selecionado
    st.markdown('<div class="legend-item"><div class="legend-color" style="background:#2B7CE9; border:1px solid #000"></div>SELECIONADO</div>', unsafe_allow_html=True)
    for area, color in area_color.items():
        st.markdown(f'<div class="legend-item"><div class="legend-color" style="background:{color}"></div>{area}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    # Filtragem de dados
    if area_sel == "Empresa inteira": df_view = df
    else:
        df_area = df[df["ÁREA"] == area_sel]
        lideres = df_area["LIDER DIRETO"].unique()
        df_view = pd.concat([df_area, df[df["NOME"].isin(lideres)]]).drop_duplicates(subset=["NOME"])

    nodes = []
    for _, row in df_view.iterrows():
        n, c = row["NOME"], row["CARGO"].upper()
        if "CEO" in c or "FOUNDER" in c: fs, mg, bw = 65, 50, 9
        elif any(x in c for x in ["DIRETOR", "GERENTE", "HEAD", "COORDENADOR", "LEAD"]): fs, mg, bw = 48, 38, 7
        else: fs, mg, bw = 38, 28, 5
        
        cor_b = area_color.get(row["ÁREA"], "#7443F6")
        cor_f = "#000000"
        if n == busca_nome: cor_b, cor_f = "#2B7CE9", "#FFFFFF"

        nodes.append({
            "id": n, "label": f"<b>{n}</b>\n{row['CARGO']}",
            "color": {"background": cor_b, "border": escurecer_cor(cor_b)},
            "font": {"multi": "html", "color": cor_f, "size": fs, "face": "Manrope"},
            "shape": "box", "margin": mg, "borderWidth": bw, "shadow": True
        })

    edges = [{"from": r["LIDER DIRETO"], "to": r["NOME"], "arrows": "to", "color": "#888888", "width": 5} 
             for _, r in df_view.iterrows() if r["LIDER DIRETO"] in df_view["NOME"].values]

    html_vis = f"""
    <div id="loading-overlay">
        <div class="spinner"></div>
        <div style="font-weight:700; color:#7443F6; font-family:sans-serif;">Montando o organograma...</div>
        <div style="color:#999; margin-top:10px; font-family:sans-serif; font-size:0.8rem;">Estabilizando posições</div>
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
                forceAtlas2Based: {{ gravitationalConstant: -4500, centralGravity: 0.005, springLength: 650, avoidOverlap: 1 }},
                stabilization: {{ iterations: 350 }}
            }},
            interaction: {{ dragNodes: true, zoomView: true, dragView: true }}
        }};
        
        var network = new vis.Network(container, data, options);

        function hideLoading() {{
            document.getElementById('loading-overlay').style.opacity = '0';
            setTimeout(() => {{ document.getElementById('loading-overlay').style.display = 'none'; }}, 800);
        }}

        // Mantém o carregamento por 10 segundos
        setTimeout(hideLoading, 10000);

        // Clique para selecionar e filtrar automaticamente
        network.on("click", function (params) {{
            if (params.nodes.length > 0) {{
                var nome = params.nodes[0];
                var url = new URL(window.parent.location.href);
                url.searchParams.set("colab", nome);
                window.parent.location.href = url.href;
            }}
        }});

        var search = "{busca_nome}";
        network.once('stabilized', function() {{
            if(search !== "Nenhum selecionado") {{
                network.focus(search, {{ scale: 0.35, animation: true }});
                network.selectNodes([search]);
            }} else {{ network.fit(); }}
        }});
    </script>
    """
    components.html(html_vis, height=880)
