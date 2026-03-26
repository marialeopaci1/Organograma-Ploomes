import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import re
import colorsys
import unicodedata
# 1. Configuração de Layout
st.set_page_config(page_title="Portal RH | Ploomes", layout="wide", initial_sidebar_state="collapsed")
def _normalizar_nome(texto):
    """Remove acentos e converte para maiúsculo para comparação."""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    sem_acento = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.upper().strip()

def _resolver_lider(lider, lista_nomes):
    """Mapeia nome abreviado do LIDER DIRETO para o NOME completo na base."""
    if not lider:
        return lider
    # Se já existe match exato, retorna como está
    if lider in lista_nomes:
        return lider
    STOP = {'DE', 'DO', 'DA', 'DOS', 'DAS', 'E'}
    palavras_lider = [p for p in _normalizar_nome(lider).split() if p not in STOP]
    if not palavras_lider:
        return lider
    candidatos = []
    for nome in lista_nomes:
        nome_norm = _normalizar_nome(nome)
        palavras_nome = nome_norm.split()
        palavras_nome_set = set(palavras_nome)
        # Todas as palavras do lider devem estar presentes no nome completo
        if all(p in palavras_nome_set for p in palavras_lider):
            primeiro_coincide = palavras_nome[0] == palavras_lider[0]
            candidatos.append((nome, primeiro_coincide, len(palavras_nome)))
    if not candidatos:
        return lider  # sem match — mantém original (não criará aresta)
    # Prioriza: primeiro nome coincide → depois menor quantidade de palavras (nome menos genérico)
    candidatos.sort(key=lambda x: (-int(x[1]), x[2]))
    return candidatos[0][0]

def escurecer_cor(hex_color, fator=0.15):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    hls = colorsys.rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    new_rgb = colorsys.hls_to_rgb(hls[0], max(0, hls[1] - fator), min(1, hls[2] + 0.1))
    return '#%02x%02x%02x' % (int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255))
# --- CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
header {visibility: hidden !important;}
.block-container { padding-top: 1.5rem !important; }
.info-box {
    background-color: #fcfcfc;
    border-radius: 15px;
    padding: 20px;
    border-left: 6px solid #6347ff;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}
.info-label { color: #6347ff; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; }
.info-text { color: #444; font-size: 0.95rem; line-height: 1.5; }
.legend-container {
    background-color: #ffffff;
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    border: 1px solid #eee;
}
.legend-item { display: flex; align-items: center; margin-bottom: 10px; font-size: 0.85rem; font-weight: 600; }
.legend-color { width: 22px; height: 22px; border-radius: 6px; margin-right: 12px; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)
if "logado" not in st.session_state:
    st.session_state.logado = False
if not st.session_state.logado:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<br><br><div style="background:white; padding:50px; border-radius:30px; text-align:center; box-shadow:0 15px 35px rgba(0,0,0,0.2); border-top:10px solid #6347ff;">', unsafe_allow_html=True)
        st.title("Ploomes")
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA"):
            if u == "RHPloomes" and s == "RHPloomes":
                st.session_state.logado = True
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
else:
    @st.cache_data(ttl=10)
    def carregar():
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTLRqVZ9LWZMaPQ9MFGvOcQ8i-_ljOeKPO8w1jpwTscup0VM1ERFYgwitfmH0Zjfo-u9-fjfd60goF1/pub?output=csv"
        df = pd.read_csv(url, sep=",")
        df.columns = df.columns.str.strip()
        def limpar(t): return str(t).strip() if pd.notna(t) else ""
        cols = ["NOME", "CARGO", "ÁREA", "LIDER DIRETO", "Descricao_Area", "Info_Posicao", "SUB-ÁREA", "CLASSIFICAÇÃO"]
        for c in cols:
            if c in df.columns: df[c] = df[c].apply(limpar)

        df = df[df["ÁREA"] != ""]
        df["ÁREA"] = df["ÁREA"].apply(lambda x: x.upper())
        # Resolver nomes abreviados em LIDER DIRETO para o nome completo da base
        lista_nomes = df["NOME"].tolist()
        df["LIDER DIRETO"] = df["LIDER DIRETO"].apply(lambda l: _resolver_lider(l, lista_nomes))
        return df
    try:
        df = carregar()
        if "area_selecionada" not in st.session_state:
            st.session_state.area_selecionada = "Empresa inteira"
        c1, c2, c3 = st.columns([2, 2, 0.8])
        with c2:
            busca_nome = st.selectbox("Localizar Colaborador:", ["Nenhum selecionado"] + sorted(df["NOME"].unique().tolist()))
            if busca_nome != "Nenhum selecionado":
                st.session_state.area_selecionada = df[df["NOME"] == busca_nome]["ÁREA"].values[0]
        with c1:
            opcoes_area = ["Empresa inteira"] + sorted(df["ÁREA"].unique().tolist())
            area_sel = st.selectbox("Área de Visão:", opcoes_area, index=opcoes_area.index(st.session_state.area_selecionada))
            st.session_state.area_selecionada = area_sel
        with c3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("SAIR"):
                st.session_state.logado = False
                st.rerun()
        if busca_nome != "Nenhum selecionado":
            pessoa = df[df["NOME"] == busca_nome].iloc[0]
            i1, i2 = st.columns(2)
            with i1: st.markdown(f'<div class="info-box"><div class="info-label">DESCRIÇÃO DA ÁREA: {pessoa["ÁREA"]}</div><div class="info-text">{pessoa["Descricao_Area"]}</div></div>', unsafe_allow_html=True)
            with i2: st.markdown(f'<div class="info-box"><div class="info-label">INFO DA POSIÇÃO: {pessoa["CARGO"]}</div><div class="info-text">{pessoa["Info_Posicao"]}</div></div>', unsafe_allow_html=True)
        df_view = df.copy() if area_sel == "Empresa inteira" else pd.concat([df[df["ÁREA"] == area_sel], df[df["NOME"].isin(df[df["ÁREA"] == area_sel]["LIDER DIRETO"].unique())]]).drop_duplicates()
        palette = ["#FF00FF", "#00FFFF", "#FFFF00", "#FF4500", "#32CD32", "#7B68EE", "#FF1493", "#A9A9A9", "#ADFF2F", "#FFD700"]
        unique_areas = sorted(df["ÁREA"].unique())
        area_color = {a: palette[i % len(palette)] for i, a in enumerate(unique_areas)}
        col_legenda, col_organograma = st.columns([1, 4.5])
        with col_legenda:
            st.markdown('<div class="legend-container"><div style="font-weight:900; margin-bottom:15px; font-size: 0.9rem;">LEGENDA</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="legend-item"><div class="legend-color" style="background:#000000"></div>COLABORADOR SELECIONADO</div>', unsafe_allow_html=True)
            st.markdown('<hr style="margin: 10px 0; border: 0; border-top: 1px solid #eee;">', unsafe_allow_html=True)
            for area, color in area_color.items():
                if area.strip():
                    st.markdown(f'<div class="legend-item"><div class="legend-color" style="background:{color}"></div>{area}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col_organograma:
            nodes = []
            for _, row in df_view.iterrows():
                nome, cargo = row["NOME"], row["CARGO"]
                is_ceo = "CEO" in cargo.upper() or "EID" in nome.upper()
                is_lider = any(x in cargo.upper() for x in ["GERENTE", "DIRETOR", "HEAD", "LEAD", "COORDENADOR"])

                size, width, border_w, margin = (300, 2000, 15, 60) if is_ceo else (180, 1400, 10, 45) if is_lider else (120, 900, 4, 30)

                cor_base = area_color.get(row["ÁREA"], "#6347ff")
                cor_fonte = "#000000"
                cor_borda = escurecer_cor(cor_base) if (is_ceo or is_lider) else cor_base

                if busca_nome != "Nenhum selecionado" and nome == busca_nome:
                    cor_base = "#000000"
                    cor_fonte = "#FFFFFF"
                    cor_borda = "#000000"
                nodes.append({
                    "id": nome, "label": f"{nome}|{cargo}",
                    "color": {"background": cor_base, "border": cor_borda},
                    "font": {"color": cor_fonte, "size": size, "face": "Inter", "multi": "md", "bold": {"color": cor_fonte}},
                    "widthConstraint": {"maximum": width}, "borderWidth": border_w, "shadow": True,
                    "margin": margin
                })

            edges = [{"from": row["LIDER DIRETO"], "to": row["NOME"], "arrows": "to", "color": "#000000", "width": 8}
                     for _, row in df_view.iterrows() if row["LIDER DIRETO"] and row["LIDER DIRETO"] in df_view["NOME"].values]
            html_vis = f"""
            <div id="loading" style="height:850px; width:100%; background:#ffffff; border-radius:20px;
                display:flex; align-items:center; justify-content:center; flex-direction:column; gap:16px;">
                <div style="width:48px;height:48px;border:5px solid #eee;border-top-color:#6347ff;
                    border-radius:50%;animation:spin 0.8s linear infinite;"></div>
                <span style="color:#6347ff;font-family:Inter,sans-serif;font-weight:700;font-size:1rem;">
                    Montando organograma...</span>
            </div>
            <div id="network" style="height:850px; width:100%; background:#ffffff; border-radius:20px; display:none;"></div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <script>
            var nodesRaw = {json.dumps(nodes)};
            nodesRaw.forEach(node => {{ var p = node.label.split('|'); node.label = '*' + p[0] + '*\\n\\n' + p[1]; }});

            var options = {{
                nodes: {{ shape: "box", font: {{ face: 'Inter', multi: 'md' }} }},
                physics: {{
                    enabled: true,
                    solver: "forceAtlas2Based",
                    forceAtlas2Based: {{
                        gravitationalConstant: -40000,
                        centralGravity: 0.005,
                        springLength: 1500,
                        avoidOverlap: 1
                    }},
                    stabilization: {{ enabled: false }}
                }}
            }};

            var network = new vis.Network(
                document.getElementById("network"),
                {{ nodes: new vis.DataSet(nodesRaw), edges: new vis.DataSet({json.dumps(edges)}) }},
                options
            );

            // Estabilização headless: roda a física internamente sem renderizar frames.
            // Muito mais rápida e não depende de requestAnimationFrame,
            // então funciona normalmente mesmo com a aba em segundo plano.
            network.stabilize(500);

            network.on("stabilized", function () {{
                network.setOptions({{ physics: false }});
                document.getElementById("loading").style.display = "none";
                document.getElementById("network").style.display = "block";
                var b = "{busca_nome}";
                if (b !== "Nenhum selecionado") {{
                    network.selectNodes([b]);
                    network.focus(b, {{ scale: 0.3, animation: true }});
                }}
            }});
            </script>
            """
            components.html(html_vis, height=900)
    except Exception as e: st.error(f"Erro: {e}")
