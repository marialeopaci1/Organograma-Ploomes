import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import colorsys

# --- 1. CONFIGURAÇÃO INICIAL E LOGIN ---
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

# --- 3. ESTADO E CALLBACKS ---
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

def voltar_empresa_inteira():
    st.session_state.sel_area = "Empresa inteira"
    st.session_state.sel_nome = "Nenhum selecionado"

def escurecer_cor(hex_color, fator=0.20):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    hls = colorsys.rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    new_rgb = colorsys.hls_to_rgb(hls[0], max(0, hls[1] - fator), min(1, hls[2] + 0.1))
    return '#%02x%02x%02x' % (int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255))

# --- 4. INTERFACE SUPERIOR ---
c1, c2, c3, c4 = st.columns([2, 2, 1, 0.6])
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
    st.button("🌐 VOLTAR PARA EMPRESA INTEIRA", on_click=voltar_empresa_inteira, use_container_width=True)
with c4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("SAIR", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

# --- 5. DESCRIÇÕES DA PLANILHA (CORRIGIDO) ---
if st.session_state.sel_area != "Empresa inteira" or st.session_state.sel_nome != "Nenhum selecionado":
    st.markdown("---")
    i1, i2 = st.columns(2)
    with i1:
        # Puxa a descrição da área selecionada ou da área do colaborador selecionado
        area_atual = st.session_state.sel_area
        dados_area = df[df["ÁREA"] == area_atual]
        if not dados_area.empty:
            # Puxa da coluna 'Descricao_Area' da planilha
            desc = dados_area["Descricao_Area"].iloc[0]
            if desc:
                st.info(f"**Sobre a área {area_atual}:**\n\n{desc}")
    with i2:
        # Puxa a info da posição do colaborador selecionado
        if st.session_state.sel_nome != "Nenhum selecionado":
            dados_colab = df[df["NOME"] == st.session_state.sel_nome]
            if not dados_colab.empty:
                # Puxa da coluna 'Info_Posicao' da planilha
                pos_info = dados_colab["Info_Posicao"].iloc[0]
                if pos_info:
                    st.success(f"**Posição de {st.session_state.sel_nome}:**\n\n{pos_info}")
    st.markdown("---")

# --- 6. ORGANOGRAMA ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');
html, body, [class*="st-"] { font-family: 'Manrope', sans-serif; }
.legend-sidebar { background: white; border-radius: 12px; padding: 15px; border: 1px solid #eee; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.legend-item { display: flex; align-items: center; margin-bottom: 8px; font-size: 0.85rem; font-weight: 700; }
.legend-color { width: 18px; height: 18px; border-radius: 4px; margin-right: 12px; border: 1px solid rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

col_side, col_main = st.columns([0.8, 5])

palette = ["#FF00FF","#00FFFF","#FFFF00","#FF4500","#32CD32","#7B68EE","#FF1493","#A9A9A9","#ADFF2F","#FFD700"]
area_color = {a: palette[i % len(palette)] for i, a in enumerate(lista_areas)}

with col_side:
    st.markdown('<div class="legend-sidebar"><b>LEGENDA</b><br><br>', unsafe_allow_html=True)
    st.markdown('<div class="legend-item"><div class="legend-color" style="background:#2B7CE9"></div>SELECIONADO</div>', unsafe_allow_html=True)
    for area, color in area_color.items():
        st.markdown(f'<div class="legend-item"><div class="legend-color" style="background:{color}"></div>{area}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    if st.session_state.sel_area == "Empresa inteira":
        df_view = df
        repulsao = -1200 # Reduzido para aproximar os cards
        distancia_mola = 180 # Reduzido para aproximar os cards
    else:
        df_view = df[df["ÁREA"] == st.session_state.sel_area]
        lideres_nomes = df_view["LIDER DIRETO"].unique()
        df_view = pd.concat([df_view, df[df["NOME"].isin(lideres_nomes)]]).drop_duplicates(subset=["NOME"])
        repulsao = -700
        distancia_mola = 150

    nodes = []
    for _, row in df_view.iterrows():
        n = row["NOME"]
        cor_b = area_color.get(row["ÁREA"], "#7443F6")
        cor_f = "#000000"
        
        # Destaque para o selecionado
        if n == st.session_state.sel_nome: 
            cor_b, cor_f = "#2B7CE9", "#FFFFFF"

        nodes.append({
            "id": n, 
            "label": f"<b>{n}</b>\n{row['CARGO']}",
            "color": {"background": cor_b, "border": escurecer_cor(cor_b)},
            # TAMANHO DA LETRA AUMENTADO PARA 26 (Nome) e mantido proporcional
            "font": {"multi": "html", "color": cor_f, "face": "Manrope", "size": 26},
            "shape": "box", 
            "margin": 18,
            "borderWidth": 2
        })

    edges = [{"from": r["LIDER DIRETO"], "to": r["NOME"], "arrows": "to", "color": "#BBBBBB", "width": 1.5} 
             for _, r in df_view.iterrows() if r["LIDER DIRETO"] in df_view["NOME"].values]

    html_vis = f"""
    <div id="mynetwork" style="height: 750px; background: white; border-radius:15px; border: 1px solid #f0f0f0;"></div>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script>
        var container = document.getElementById('mynetwork');
        var data = {{ nodes: new vis.DataSet({json.dumps(nodes)}), edges: new vis.DataSet({json.dumps(edges)}) }};
        var options = {{
            physics: {{
                enabled: true,
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {{ 
                    gravitationalConstant: {repulsao}, 
                    centralGravity: 0.005, 
                    springLength: {distancia_mola}, 
                    avoidOverlap: 1 
                }},
                stabilization: {{ iterations: 150 }}
            }},
            interaction: {{ dragNodes: true, zoomView: true, dragView: true, hover: true }}
        }};
        var network = new vis.Network(container, data, options);
        
        network.once('stabilized', function() {{
            var search = "{st.session_state.sel_nome}";
            if(search !== "Nenhum selecionado") {{
                network.focus(search, {{ scale: 0.7, animation: true }});
            }} else {{
                network.fit();
            }}
        }});
    </script>
    """
    components.html(html_vis, height=770)
