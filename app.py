with col_main:
    is_full = st.session_state.sel_area == "Empresa inteira"
    
    # Ajuste de escala para o layout hierárquico
    if is_full:
        df_view = df
        repulsao = -10000
    else:
        df_view = df[df["ÁREA"] == st.session_state.sel_area].copy()
        l_norm = df_view["LIDER_NORM"].unique()
        df_view = pd.concat([df_view, df[df["NOME_NORM"].isin(l_norm)]]).drop_duplicates(subset=["NOME"])
        repulsao = -2000

    nodes = []
    for _, row in df_view.iterrows():
        n = row["NOME"]
        is_ceo = "CEO" in row["CARGO"].upper() or "MATHEUS EID PAGANI" in n.upper()
        # Reduzi um pouco o tamanho do CEO para o layout vertical não ficar gigante
        t_f, m_i, l_m, b = (60, 35, 500, 6) if is_ceo else (28, 15, 250, 2)
        c_b = area_color.get(row["ÁREA"], "#7443F6")
        c_f = "#FFFFFF" if n == st.session_state.sel_nome else "#000000"
        if n == st.session_state.sel_nome: c_b = "#2B7CE9"

        nodes.append({
            "id": row["NOME_NORM"], 
            "label": f"<b>{n}</b>\n{row['CARGO']}", 
            "color": {"background": c_b, "border": escurecer_cor(c_b)}, 
            "font": {"multi": "html", "color": c_f, "size": t_f, "face": "Manrope"}, 
            "shape": "box", 
            "margin": m_i, 
            "borderWidth": b, 
            "widthConstraint": {"maximum": l_m}
        })

    edges = [{"from": r["LIDER_NORM"], "to": r["NOME_NORM"], "arrows": "to", "color": "#000000", "width": 2} 
             for _, r in df_view.iterrows() if r["LIDER_NORM"] in df_view["NOME_NORM"].values]

    html_vis = f"""
    <div id="loading" style="position:absolute; width:100%; height:100%; background:white; display:flex; flex-direction:column; align-items:center; justify-content:center; z-index:999; font-family:sans-serif;">
        <div style="width:40px; height:40px; border:4px solid #f3f3f3; border-top:4px solid #7443F6; border-radius:50%; animation:spin 1s linear infinite;"></div>
        <p style="margin-top:10px; font-weight:bold; color:#7443F6;">Gerando Layout Hierárquico...</p>
    </div>
    <div id="mynetwork" style="height: 800px; background: white; border-radius:15px; border: 1px solid #ddd;"></div>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script>
        var container = document.getElementById('mynetwork');
        var data = {{ nodes: new vis.DataSet({json.dumps(nodes)}), edges: new vis.DataSet({json.dumps(edges)}) }};
        var options = {{ 
            layout: {{
                hierarchical: {{
                    enabled: true,
                    direction: 'UD',        // UD = Up-Down (Cima para Baixo)
                    sortMethod: 'directed', // Mantém a hierarquia da planilha
                    nodeSpacing: 300,       // Espaço entre cards do mesmo nível
                    levelSeparation: 400    // Espaço entre níveis (Cargos)
                }}
            }},
            physics: {{ 
                hierarchicalRepulsion: {{
                    nodeDistance: 350,
                    avoidOverlap: 1
                }}
            }},
            interaction: {{ 
                dragNodes: false, // Em layout hierárquico é melhor travar os nós
                zoomView: true, 
                dragView: true 
            }} 
        }};
        var network = new vis.Network(container, data, options);
        
        network.once('stabilized', function() {{ 
            var sN = "{normalizar_nome(st.session_state.sel_nome)}";
            if(sN !== "{normalizar_nome('Nenhum selecionado')}") network.focus(sN, {{ scale: 0.6, animation: true }});
            document.getElementById('loading').style.display = 'none'; 
        }});
        
        setTimeout(() => {{ document.getElementById('loading').style.display = 'none'; }}, 8000);
    </script>
    <style>@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>
    """
    components.html(html_vis, height=820)
