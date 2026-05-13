with col_main:
    is_full = st.session_state.sel_area == "Empresa inteira"
    
    if is_full:
        df_view = df
        # Aumentamos drasticamente a repulsão e o espaço para a empresa inteira
        repulsao = -15000 
        mola = 400
        solver = 'barnesHut'
        gravidade_central = 0.05
    else:
        df_view = df[df["ÁREA"] == st.session_state.sel_area].copy()
        l_norm = df_view["LIDER_NORM"].unique()
        df_view = pd.concat([df_view, df[df["NOME_NORM"].isin(l_norm)]]).drop_duplicates(subset=["NOME"])
        # Valores que você já aprovou para as áreas
        repulsao = -1500
        mola = 250
        solver = 'forceAtlas2Based'
        gravidade_central = 0.005

    nodes = []
    for _, row in df_view.iterrows():
        n = row["NOME"]
        is_ceo = "CEO" in row["CARGO"].upper() or "MATHEUS EID PAGANI" in n.upper()
        t_f, m_i, l_m, b = (80, 45, 600, 8) if is_ceo else (28, 15, 250, 2)
        c_b = area_color.get(row["ÁREA"], "#7443F6")
        c_f = "#FFFFFF" if n == st.session_state.sel_nome else "#000000"
        if n == st.session_state.sel_nome: c_b = "#2B7CE9"

        nodes.append({
            "id": row["NOME_NORM"], "label": f"<b>{n}</b>\n{row['CARGO']}", 
            "color": {"background": c_b, "border": escurecer_cor(c_b)}, 
            "font": {"multi": "html", "color": c_f, "size": t_f, "face": "Manrope"}, 
            "shape": "box", "margin": m_i, "borderWidth": b, "widthConstraint": {"maximum": l_m}
        })

    edges = [{"from": r["LIDER_NORM"], "to": r["NOME_NORM"], "arrows": "to", "color": "#000000", "width": 3} 
             for _, r in df_view.iterrows() if r["LIDER_NORM"] in df_view["NOME_NORM"].values]

    html_vis = f"""
    <div id="loading" style="position:absolute; width:100%; height:100%; background:white; display:flex; flex-direction:column; align-items:center; justify-content:center; z-index:999; font-family:sans-serif;">
        <div style="width:40px; height:40px; border:4px solid #f3f3f3; border-top:4px solid #7443F6; border-radius:50%; animation:spin 1s linear infinite;"></div>
        <p style="margin-top:10px; font-weight:bold; color:#7443F6;">Organizando {len(nodes)} colaboradores...</p>
    </div>
    <div id="mynetwork" style="height: 750px; background: white; border-radius:15px; border: 1px solid #ddd;"></div>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script>
        var container = document.getElementById('mynetwork');
        var data = {{ nodes: new vis.DataSet({json.dumps(nodes)}), edges: new vis.DataSet({json.dumps(edges)}) }};
        var options = {{ 
            physics: {{ 
                enabled: true, 
                solver: '{solver}', 
                barnesHut: {{ gravitationalConstant: {repulsao}, centralGravity: {gravidade_central}, springLength: {mola}, avoidOverlap: 1 }},
                forceAtlas2Based: {{ gravitationalConstant: {repulsao}, centralGravity: {gravidade_central}, springLength: {mola}, avoidOverlap: 1 }},
                stabilization: {{ enabled: true, iterations: 300 }} 
            }}, 
            interaction: {{ dragNodes: true, zoomView: true, dragView: true }} 
        }};
        var network = new vis.Network(container, data, options);
        
        network.on('stabilizationProgress', function(params) {{
            if (params.iterations > 280) {{
                network.stopSimulation();
                document.getElementById('loading').style.display = 'none';
            }}
        }});

        network.once('stabilizationIterationsDone', function() {{ 
            network.setOptions({{ physics: false }});
            var sN = "{normalizar_nome(st.session_state.sel_nome)}";
            if(sN !== "{normalizar_nome('Nenhum selecionado')}") network.focus(sN, {{ scale: 0.7, animation: true }});
            document.getElementById('loading').style.display = 'none'; 
        }});
        
        setTimeout(() => {{ 
            network.stopSimulation();
            document.getElementById('loading').style.display = 'none'; 
        }}, 8000);
    </script>
    <style>@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>
    """
    components.html(html_vis, height=770)
