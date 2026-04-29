import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import colorsys
import unicodedata

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

# --- FUNÇÃO DE NORMALIZAÇÃO (A MUDANÇA SOLICITADA) ---
def normalizar_nome(nome):
    if not nome: return ""
    nome = str(nome).upper().strip()
    # Caso específico do Barba
    if "LUIZ FERNANDO BARBA" in nome:
        return "LUIZ FERNANDO BARBA"
    # Remove acentos
    return "".join(c for c in unicodedata.normalize('NFD', nome) if unicodedata.category(c) != 'Mn')

# --- 2. CARGA DE DADOS ---
@st.cache_data(ttl=3600)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTLRqVZ9LWZMaPQ9MFGvOcQ8i-_ljOeKPO8w1jpwTscup0VM1ERFYgwitfmH0Zjfo-u9-fjfd60goF1/pub?output=csv"
    df = pd.read_csv(url).fillna("")
    df.columns = df.columns.str.strip()
    
    for col in ["ÁREA", "NOME", "LIDER DIRETO", "Descricao_Area", "Info_Posicao"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    df["ÁREA_BUSCA"] = df["ÁREA"].str.upper()
    # Criamos colunas normalizadas para fazer o "Match" da hierarquia sem erro de acento ou nome curto
    df["NOME_NORM"] = df["NOME"].apply(normalizar_nome)
    df["LIDER_NORM"] = df["LIDER DIRETO"].apply(normalizar_nome)
    
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

# --- 5. QUADROS ROXOS ---
st.markdown("<style>.stAlert { background-color: #f3f0ff !important; border: 1px solid #7443F6 !important; color: #2e1065 !important; border-radius: 10px !important; }</style>", unsafe_allow_html=True)

if st.session_state.sel_area != "Empresa inteira" or st.session_state.sel_nome != "Nenhum selecionado":
    st.markdown("<br>", unsafe_allow_html=True)
    inf1, inf2 = st.columns(2)
    area_para_pesquisa = st.session_state.sel_area
    if st.session_state.sel_nome != "Nenhum selecionado":
        area_para_pesquisa = nome_para_area.get(st.session_state.sel_nome, st.session_state.sel_area)

    with inf1:
        if area_para_pesquisa != "Empresa inteira":
            dados_area = df[(df["ÁREA"] == area_para_pesquisa) & (df["Descricao_Area"] != "") & (df["Descricao_Area"] != "nan")]
            if not dados_area.empty:
                st.info(f"**🏢 Sobre a área {area_para_pesquisa}:**\n\n{dados_area['Descricao_Area'].iloc[0]}")
    with inf2:
        if st.session_state.sel_nome != "Nenhum selecionado":
            dados_colab = df[df["NOME"] == st.session_state.sel_nome]
            if not dados_colab.empty:
                texto_pos = dados_colab["Info_Posicao"].iloc[0]
                if texto_pos and texto_pos.lower() != "nan" and texto_pos != "":
                    st.info(f"**👤 Posição de {st.session_state.sel_nome}:**\n\n{texto_pos}")
    st.markdown("---")

# --- 6. ORGANOGRAMA ---
col_side, col_main = st.columns([0.8, 5])
palette = ["#FF00FF","#00FFFF","#FFFF00","#FF4500","#32CD32","#7B68EE","#FF1493","#A9A9A9","#ADFF2F","#FFD700"]
area_color = {a: palette[i % len(palette)] for i, a in enumerate(lista_areas)}

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
        df_view = df[df["ÁREA"] == st.session_state.sel_area].copy()
        lideres_norm = df_view["LIDER_NORM"].unique()
        df_view = pd.concat([df_view, df[df["NOME_NORM"].isin(lideres_norm)]]).drop_duplicates(subset=["NOME"])
        repulsao = -850

    nodes = []
    for _, row in df_view.iterrows():
        n = row["NOME"]
        cor_b = area_color.get(row["ÁREA"], "#7443F6")
        cor_f = "#000000"
        if n == st.session_state.sel_nome: cor_b, cor_f = "#2B7CE9", "#FFFFFF"
        nodes.append({"id": row["NOME_NORM"], "label": f"<b>{n}</b>\n{row['CARGO']}", "color": {"background": cor_b, "border": "#333333"}, "font": {"multi": "html", "color": cor_f, "size": 28}, "shape": "box", "margin": 15})

    # Hierarquia baseada nas colunas NORMALIZADAS
    edges = [{"from": r["LIDER_NORM"], "to": r["NOME_NORM"], "arrows": "to", "color": "#000000", "width": 3} 
             for _, r in df_view.iterrows() if r["LIDER_NORM"] in df_view["NOME_NORM"].values]

    html_vis = f"""
    <div id="loading" style="position:absolute; width:100%; height:100%; background:white; display:flex; align-items:center; justify-content:center; z-index:999; font-family:sans-serif;">
        <div style="text-align:center;"><div style="width:40px; height:40px; border:4px solid #f3f3f3; border-top:4px solid #7443F6; border-radius:50%; animation:spin 1s linear infinite;"></div><p style="margin-top:10px; font-weight:bold; color:#7443F6;">Montando o organograma...</p></div>
    </div>
    <div id="mynetwork" style="height: 750px; background: white; border-radius:15px; border: 1px solid #ddd;"></div>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script>
        var container = document.getElementById('mynetwork');
        var data = {{ nodes: new vis.DataSet({json.dumps(nodes)}), edges: new vis.DataSet({json.dumps(edges)}) }};
        var options = {{ physics: {{ enabled: true, solver: 'forceAtlas2Based', forceAtlas2Based: {{ gravitationalConstant: {repulsao}, springLength: 180, avoidOverlap: 1 }}, stabilization: {{ iterations: 200 }} }}, interaction: {{ dragNodes: true, zoomView: true, dragView: true }} }};
        var network = new vis.Network(container, data, options);
        network.once('stabilized', function() {{ 
            var searchNorm = "{normalizar_nome(st.session_state.sel_nome)}";
            if(searchNorm !== "{normalizar_nome('Nenhum selecionado')}") network.focus(searchNorm, {{ scale: 0.7, animation: true }});
            document.getElementById('loading').style.display = 'none'; 
        }});
        setTimeout(() => {{ document.getElementById('loading').style.display = 'none'; }}, 5000);
    </script>
    """
    components.html(html_vis, height=770)
