import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import colorsys
import unicodedata

st.set_page_config(page_title="Portal RH | Ploomes", layout="wide", initial_sidebar_state="collapsed")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalizar_nome(texto):
    nfkd = unicodedata.normalize('NFKD', str(texto))
    sem_acento = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.upper().strip()

def _resolver_lider(lider, lista_nomes):
    if not lider:
        return lider
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
        if all(p in set(palavras_nome) for p in palavras_lider):
            candidatos.append((nome, palavras_nome[0] == palavras_lider[0], len(palavras_nome)))
    if not candidatos:
        return lider
    candidatos.sort(key=lambda x: (-int(x[1]), x[2]))
    return candidatos[0][0]

def escurecer_cor(hex_color, fator=0.15):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    hls = colorsys.rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    new_rgb = colorsys.hls_to_rgb(hls[0], max(0, hls[1] - fator), min(1, hls[2] + 0.1))
    return '#%02x%02x%02x' % (int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255))

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }
header { visibility: hidden !important; }
.block-container { padding-top: 1rem !important; padding-bottom: 0 !important; }
.info-box {
    background: #fcfcfc; border-radius: 15px; padding: 20px;
    border-left: 6px solid #7443F6; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 16px;
}
.info-label { color: #7443F6; font-size: 0.82rem; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; }
.info-text  { color: #444; font-size: 0.93rem; line-height: 1.5; }
.legend-container {
    background: #fff; border-radius: 15px; padding: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #eee; margin-top: 8px;
}
.legend-item  { display: flex; align-items: center; margin-bottom: 9px; font-size: 0.82rem; font-weight: 600; }
.legend-color { width: 20px; height: 20px; border-radius: 5px; margin-right: 10px; border: 1px solid #ddd; flex-shrink: 0; }
</style>
""", unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────────────────
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<br><br><div style="background:white;padding:50px;border-radius:30px;text-align:center;box-shadow:0 15px 35px rgba(0,0,0,0.2);border-top:10px solid #7443F6;">', unsafe_allow_html=True)
        st.title("Ploomes")
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA"):
            if u == "RHPloomes" and s == "RHPloomes":
                st.session_state.logado = True
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# A partir daqui: usuário está logado
# ─────────────────────────────────────────────────────────────────────────────

# ── Carrega dados UMA vez e guarda no session_state ───────────────────────────
# Usar session_state em vez de cache_data evita o overhead de serialização
# do Streamlit e garante que as listas de opções fiquem instantâneas.
if "df" not in st.session_state:
    @st.cache_data(ttl=3600, show_spinner="Carregando colaboradores...")
    def _carregar_raw():
        url = (
            "https://docs.google.com/spreadsheets/d/e/"
            "2PACX-1vTLRqVZ9LWZMaPQ9MFGvOcQ8i-_ljOeKPO8w1jpwTscup0VM1ERFYgwitfmH0Zjfo-u9-fjfd60goF1"
            "/pub?output=csv"
        )
        df = pd.read_csv(url, sep=",")
        df.columns = df.columns.str.strip()
        def limpar(t): return str(t).strip() if pd.notna(t) else ""
        for c in ["NOME", "CARGO", "ÁREA", "LIDER DIRETO", "Descricao_Area", "Info_Posicao", "SUB-ÁREA", "CLASSIFICAÇÃO"]:
            if c in df.columns:
                df[c] = df[c].apply(limpar)
        df = df[df["ÁREA"] != ""].copy()
        df["ÁREA"] = df["ÁREA"].str.upper()
        lista_nomes = df["NOME"].tolist()
        df["LIDER DIRETO"] = df["LIDER DIRETO"].apply(lambda l: _resolver_lider(l, lista_nomes))
        return df

    st.session_state.df = _carregar_raw()

    # Pré-calcula paleta e mapa de cores (imutável após carga)
    palette = ["#FF00FF","#00FFFF","#FFFF00","#FF4500","#32CD32",
               "#7B68EE","#FF1493","#A9A9A9","#ADFF2F","#FFD700"]
    unique_areas = sorted(st.session_state.df["ÁREA"].unique())
    st.session_state.area_color = {a: palette[i % len(palette)] for i, a in enumerate(unique_areas)}

    # Pré-calcula listas de opções (strings simples — instâneas no selectbox)
    st.session_state.opcoes_area = ["Empresa inteira"] + sorted(st.session_state.df["ÁREA"].unique().tolist())
    st.session_state.opcoes_nome = ["Nenhum selecionado"] + sorted(st.session_state.df["NOME"].unique().tolist())

    # Pré-calcula mapa nome→área para lookup O(1)
    st.session_state.nome_para_area = dict(zip(st.session_state.df["NOME"], st.session_state.df["ÁREA"]))

df         = st.session_state.df
area_color = st.session_state.area_color
opcoes_area = st.session_state.opcoes_area
opcoes_nome = st.session_state.opcoes_nome
nome_para_area = st.session_state.nome_para_area

# ── Estado dos filtros ────────────────────────────────────────────────────────
if "sel_area" not in st.session_state:
    st.session_state.sel_area = "Empresa inteira"
if "sel_nome" not in st.session_state:
    st.session_state.sel_nome = "Nenhum selecionado"

# ── Callbacks — executam ANTES do próximo render ─────────────────────────────
def ao_mudar_area():
    st.session_state.sel_area = st.session_state._w_area
    st.session_state.sel_nome = "Nenhum selecionado"   # limpa colaborador

def ao_mudar_nome():
    nome = st.session_state._w_nome
    st.session_state.sel_nome = nome
    if nome != "Nenhum selecionado":
        # Lookup O(1) — sem varredura no DataFrame
        st.session_state.sel_area = nome_para_area.get(nome, st.session_state.sel_area)

# ── Barra de controles ────────────────────────────────────────────────────────
col_a, col_n, col_sair = st.columns([2.5, 2.5, 0.6])

with col_a:
    st.selectbox(
        "🏢  Área de Visão:",
        options=opcoes_area,
        index=opcoes_area.index(st.session_state.sel_area),
        key="_w_area",
        on_change=ao_mudar_area,
    )

with col_n:
    st.selectbox(
        "🔍  Localizar Colaborador:",
        options=opcoes_nome,
        index=opcoes_nome.index(st.session_state.sel_nome),
        key="_w_nome",
        on_change=ao_mudar_nome,
    )

with col_sair:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("SAIR", use_container_width=True):
        # Limpa tudo do session_state ao sair
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ── Valores consolidados ──────────────────────────────────────────────────────
area_sel   = st.session_state.sel_area
busca_nome = st.session_state.sel_nome

# ── Info boxes ────────────────────────────────────────────────────────────────
if busca_nome != "Nenhum selecionado":
    pessoa = df[df["NOME"] == busca_nome].iloc[0]
    i1, i2 = st.columns(2)
    with i1:
        st.markdown(
            f'<div class="info-box"><div class="info-label">DESCRIÇÃO DA ÁREA: {pessoa["ÁREA"]}</div>'
            f'<div class="info-text">{pessoa["Descricao_Area"]}</div></div>',
            unsafe_allow_html=True)
    with i2:
        st.markdown(
            f'<div class="info-box"><div class="info-label">INFO DA POSIÇÃO: {pessoa["CARGO"]}</div>'
            f'<div class="info-text">{pessoa["Info_Posicao"]}</div></div>',
            unsafe_allow_html=True)

# ── Filtro do DataFrame ───────────────────────────────────────────────────────
if area_sel == "Empresa inteira":
    df_view = df
else:
    df_area    = df[df["ÁREA"] == area_sel]
    lideres    = set(df_area["LIDER DIRETO"].dropna().unique())
    df_lideres = df[df["NOME"].isin(lideres)]
    df_view    = pd.concat([df_area, df_lideres]).drop_duplicates(subset=["NOME"])

# ── Layout: legenda | organograma ─────────────────────────────────────────────
col_leg, col_org = st.columns([1, 4.5])

with col_leg:
    html_leg = '<div class="legend-container">'
    html_leg += '<div style="font-weight:900;margin-bottom:12px;font-size:0.88rem;">LEGENDA</div>'
    html_leg += '<div class="legend-item"><div class="legend-color" style="background:#000000"></div>SELECIONADO</div>'
    html_leg += '<hr style="margin:8px 0;border:0;border-top:1px solid #eee;">'
    for area, color in area_color.items():
        if area.strip():
            html_leg += f'<div class="legend-item"><div class="legend-color" style="background:{color}"></div>{area}</div>'
    html_leg += '</div>'
    st.markdown(html_leg, unsafe_allow_html=True)

with col_org:
    # ── Monta nós ─────────────────────────────────────────────────────────────
    nodes = []
    for _, row in df_view.iterrows():
        nome, cargo = row["NOME"], row["CARGO"]
        is_ceo   = "CEO" in cargo.upper() or "EID" in nome.upper()
        is_lider = any(x in cargo.upper() for x in ["GERENTE","DIRETOR","HEAD","LEAD","COORDENADOR"])

        size, width, border_w, margin = (
            (300, 2000, 15, 60) if is_ceo else
            (180, 1400, 10, 45) if is_lider else
            (120, 900,  4,  30)
        )

        cor_base  = area_color.get(row["ÁREA"], "#7443F6")
        cor_fonte = "#000000"
        cor_borda = escurecer_cor(cor_base) if (is_ceo or is_lider) else cor_base

        if busca_nome != "Nenhum selecionado" and nome == busca_nome:
            cor_base, cor_fonte, cor_borda = "#000000", "#FFFFFF", "#000000"

        nodes.append({
            "id":    nome,
            "label": f"{nome}|{cargo}",
            "color": {"background": cor_base, "border": cor_borda},
            "font":  {"color": cor_fonte, "size": size, "face": "Manrope", "multi": "md", "bold": {"color": cor_fonte}},
            "widthConstraint": {"maximum": width},
            "borderWidth": border_w,
            "shadow": True,
            "margin": margin,
        })

    # ── Monta arestas ─────────────────────────────────────────────────────────
    nomes_view = set(df_view["NOME"].values)
    edges = [
        {"from": row["LIDER DIRETO"], "to": row["NOME"], "arrows": "to", "color": "#000000", "width": 8}
        for _, row in df_view.iterrows()
        if row["LIDER DIRETO"] and row["LIDER DIRETO"] in nomes_view
    ]

    html_vis = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
* {{ margin:0;padding:0;box-sizing:border-box; }}
body {{ background:#fff;overflow:hidden; }}
#loading {{
  position:absolute;inset:0;background:#fff;border-radius:20px;
  display:flex;align-items:center;justify-content:center;
  flex-direction:column;gap:16px;z-index:10;
}}
#spinner {{
  width:48px;height:48px;border:5px solid #eee;
  border-top-color:#7443F6;border-radius:50%;
  animation:spin .8s linear infinite;
}}
#loading span {{ color:#7443F6;font-family:Manrope,sans-serif;font-weight:700;font-size:1rem; }}
#network {{ position:absolute;inset:0;background:#fff;border-radius:20px;opacity:0;transition:opacity .4s; }}
#network.visivel {{ opacity:1; }}
@keyframes spin {{ to {{ transform:rotate(360deg); }} }}
</style>
</head><body>
<div id="loading"><div id="spinner"></div><span>Montando organograma...</span></div>
<div id="network"></div>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<script>
var nodesRaw = {json.dumps(nodes)};
nodesRaw.forEach(function(n) {{
  var p = n.label.split('|');
  n.label = '*' + p[0] + '*\\n\\n' + p[1];
}});

try {{
  var _wc='setInterval(function(){{postMessage(1)}},16)';
  var _wb=new Blob([_wc],{{type:'text/javascript'}});
  var _wk=new Worker(URL.createObjectURL(_wb));
  var _rq=[];
  window.requestAnimationFrame=function(cb){{_rq.push(cb);return _rq.length;}};
  _wk.onmessage=function(){{
    var cbs=_rq.splice(0),t=performance.now();
    for(var i=0;i<cbs.length;i++){{try{{cbs[i](t);}}catch(e){{}}}}
  }};
}} catch(e) {{}}

var network = new vis.Network(
  document.getElementById("network"),
  {{ nodes: new vis.DataSet(nodesRaw), edges: new vis.DataSet({json.dumps(edges)}) }},
  {{
    nodes: {{ shape:"box", font:{{ face:'Manrope', multi:'md' }} }},
    physics: {{
      enabled:true, solver:"forceAtlas2Based",
      forceAtlas2Based:{{ gravitationalConstant:-40000, centralGravity:0.005, springLength:1500, avoidOverlap:1 }},
      stabilization:{{ enabled:true, iterations:200, fit:true }}
    }}
  }}
);

function mostrar() {{
  document.getElementById("loading").style.display="none";
  document.getElementById("network").classList.add("visivel");
  var b={json.dumps(busca_nome)};
  if(b && b!=="Nenhum selecionado") {{
    network.selectNodes([b]);
    network.focus(b,{{scale:0.3,animation:true}});
  }}
}}

setTimeout(mostrar, 5000);
network.on("stabilized", function() {{ network.setOptions({{physics:false}}); mostrar(); }});
</script>
</body></html>"""

    components.html(html_vis, height=900, scrolling=False)
