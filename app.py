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
    for col in ["ÁREA", "NOME", "Descricao_Area", "Info_Posicao"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    df["ÁREA"] = df["ÁREA"].str.upper()
    return df

df = carregar_dados()
lista_nomes = sorted(df["NOME"].unique().tolist())
lista_areas = sorted(df["ÁREA"].unique().tolist())
nome_para_area = dict(zip(df["NOME"], df["ÁREA"]))

# --- 3. ESTADO E FILTROS ---
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
    st.button("🌐 VER EMPRESA INTEIRA", on_click=voltar_empresa_inteira, use_container_width=True)
with c4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("SAIR", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

# --- 5. EXIBIÇÃO DAS DESCRIÇÕES (ROXO E CORRIGIDO) ---
# CSS para deixar os quadros roxos (estilo Ploomes)
st.markdown("""
<style>
    .stAlert { background-color: #f3f0ff; border-color: #7443F6; color: #2e1065; }
    .stAlert svg { fill: #7443F6; }
</style>
""", unsafe_allow_html=True)

if st.session_state.sel_area != "Empresa inteira" or st.session_state.sel_nome != "Nenhum selecionado":
    st.markdown("---")
    col_inf1, col_inf2 = st.columns(2)
    
    with col_inf1:
        # Se localizou alguém, a área de referência é a desse colaborador
        area_ref = st.session_state.sel_area
        if area_ref != "Empresa inteira":
            linha_area = df[df["ÁREA"] == area_ref].iloc[0]
            texto_area = linha_area.get("Descricao_Area", "")
            if texto_area and texto_area.lower() != "nan":
                st.info(f"**🏢 Sobre a área {area_ref}:**\n\n{texto_area}")

    with col_inf2:
        if st.session_state.sel_nome != "Nenhum selecionado":
            linha_colab = df[df["NOME"] == st.session_state.sel_nome].iloc[0]
            texto_pos = linha_colab.get("Info_Posicao", "")
            if texto_pos and texto_pos.lower() != "nan":
                st.info(f"**👤 Posição de {st.session_state.sel_nome}:**\n\n{texto_pos}")
    st.markdown("---")

# --- 6. ORGANOGRAMA ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');
html, body, [class*="st-"] { font-family: 'Manrope', sans-serif; }
#loading-overlay {
    position: absolute; top:0; left:0; width:100%; height:100%;
    background: white; display:flex; flex-direction:column;
    align-items:center; justify-content:center; z-index:9999;
}
.spinner {
    width: 50px; height: 50px; border: 5px solid #f3f3f3;
    border-top: 5px solid #7443F6; border-radius: 50%;
    animation: spin 1s linear infinite;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
""", unsafe_allow_html=True)

col_side, col_main = st.columns([0.8, 5])

palette = ["#FF00FF","#00FFFF","#FFFF00","#FF4500","#32CD32","#7B68EE","#FF1493","#A9A9A9","#ADFF2F","#FFD700"]
areas_unicas = sorted(df["ÁREA"].unique().tolist())
area_color = {a: palette[i % len(palette)] for i, a in enumerate(areas_unicas)}

with col_side:
    st.markdown('<div style="background:white; padding:15px; border-radius:10px; border:1px solid #eee;"><b>LEGENDA</b><br><br>', unsafe_allow_html=True)
    for area, color in area_color.items():
        st.markdown(f'<div style="display:flex; align-items:center; margin-bottom:5px;"><div style="width:15px; height:15px; background:{color}; margin-right:10px; border-radius:3px;"></div><span style="font-size:0.8rem; font-weight:700;">{area}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    if st.session_state.sel_area == "Empresa inteira":
        df_view = df
        repulsao = -1300
    else:
        df_view = df[df["ÁREA"] == st.session_state.sel_area]
        lideres = df_view["LIDER DIRETO"].unique()
        df_view = pd.concat([df_view, df[df["NOME"].isin(lideres)]]).drop_duplicates(subset=["NOME"])
        repulsao = -800

    nodes = []
    for _, row in df_view.iterrows():
        n = row["NOME"]
        cor_b = area_color.get(row["ÁREA"], "#7443F6")
        cor_f = "#000000"
        if n == st.session_state.sel_nome: cor_b, cor_f = "#2B7CE9", "#FFFFFF"

        nodes.append({
            "id": n, "label": f"<b>{n}</b>\n{row['CARGO']}",
            "color": {"background": cor_b, "border": "#333333"},
            "font": {"multi": "html", "color": cor_f, "size": 28},
            "shape": "box", "margin": 15
        })

    edges = [{"from": r["LIDER DIRETO"], "to": r["NOME"], "arrows": "to", "color": "#000000", "width": 3} 
             for _, r in df_view.iterrows() if r["LIDER DIRETO"] in df_view["NOME"].values]

    html_vis = f"""
    <div id="loading-overlay"><div class="spinner"></div><p style="margin-top:15px; font-weight:bold; color:#7443F6;">Montando o organograma...</p></div>
    <div id="mynetwork" style="height: 750px; background: white; border-radius:15px; border: 1px solid #ddd;"></div>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script>
        var container = document.getElementById('mynetwork');
        var data = {{ nodes: new vis.DataSet({json.dumps(nodes)}), edges: new vis.DataSet({json.dumps(edges)}) }};
        var options = {{
            physics: {{
                enabled: true,
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {{ gravitationalConstant: {repulsao}, centralGravity: 0.005, springLength: 180, avoidOverlap: 1 }},
                stabilization: {{ iterations: 200 }}
            }},
            interaction: {{ dragNodes: true, zoomView: true, dragView: true }}
        }};
        var network = new vis.Network(container, data, options);
        
        function hideLoading() {{
            document.getElementById('loading-overlay').style.opacity = '0';
            setTimeout(() => {{ document.getElementById('loading-overlay').style.display = 'none'; }}, 500);
        }}

        network.once('stabilized', function() {{
            var search = "{st.session_state.sel_nome}";
            if(search !== "Nenhum selecionado") {{
                network.focus(search, {{ scale: 0.7, animation: true }});
            }}
            hideLoading();
        }});
        setTimeout(hideLoading, 5000);
    </script>
    """
    components.html(html_vis, height=770)
