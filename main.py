import streamlit as st
from neo4j import GraphDatabase
import streamlit.components.v1 as components
from pyvis.network import Network
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Social Network Graph Analysis 🕸️", layout="wide")

driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")))

def run_query(query, params=None):
    with driver.session() as s:
        return list(s.run(query, params))

st.sidebar.title("Panel de Control")
menu = st.sidebar.radio("Módulo:", ["🌐 Explorador Visual", "👤 Ficha de Usuario", "🛠️ Gestión de Comunidad", "🧠 Inteligencia de Red"])

if menu == "🌐 Explorador Visual":
    st.header("Visualización Interactiva del Grafo")
    query = "MATCH (n) OPTIONAL MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 150"
    
    with driver.session() as session:
        result = session.run(query)
        net = Network(height="750px", width="100%", bgcolor="#0e1117", font_color="white", directed=True, cdn_resources='remote')
        
        added_nodes = set()
        
        for record in result:
            node_n = record["n"]
            node_m = record["m"]
            
            for node in [node_n, node_m]:
                if node and node["nombre"] not in added_nodes:
                    labels = list(node.labels)
                    
                    if "Usuario" in labels:
                        color = "#2E86C1"
                        shape = "dot"
                    else:
                        color = "#F1C40F"
                        shape = "diamond"
                    
                    net.add_node(node["nombre"], 
                                 label=node["nombre"], 
                                 color=color, 
                                 shape=shape, 
                                 physics=True,
                                 size=30)
                    added_nodes.add(node["nombre"])
            
            if node_n and node_m and record["r"] is not None:
                net.add_edge(node_n["nombre"], node_m["nombre"], color="#566573", width=1.5)

        net.set_options("""
            var options = {
            "physics": {
                "barnesHut": {
                "gravitationalConstant": -10000,
                "centralGravity": 0.3,
                "springLength": 200,
                "springConstant": 0.05,
                "damping": 0.5,
                "avoidOverlap": 1
                },
                "stabilization": {
                "enabled": true,
                "iterations": 2000
                }
            },
            "interaction": {
                "navigationButtons": true,
                "multiselect": true,
                "zoomView": true
            }
            }
            """)
        net.save_graph("grafo.html")
        components.html(open("grafo.html", 'r', encoding='utf-8').read(), height=800)


elif menu == "👤 Ficha de Usuario":
    st.header("Detalle del Usuario")
    
    col_s, col_b = st.columns([0.85, 0.15])
    with col_s:
        usuarios = [r['nombre'] for r in run_query("MATCH (u:Usuario) RETURN u.nombre AS nombre ORDER BY nombre")]
        u_sel = st.selectbox("Selecciona un perfil:", usuarios)
    with col_b:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.popover("🔍 Mostrar Query"):
            st.code("MATCH (u:Usuario) RETURN u.nombre AS nombre ORDER BY nombre", language="cypher")
    
    col1, col2 = st.columns(2)
    with col1:
        data = run_query("MATCH (u:Usuario {nombre: $n}) RETURN u", {"n": u_sel})[0]['u']
        
        c1, c2 = st.columns([0.85, 0.15])
        with c1:
            st.metric("Ciudad", data['ciudad'])
        with c2:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.popover("🔍 Query"):
                st.code(f"MATCH (u:Usuario {{nombre: '{u_sel}'}}) RETURN u (Ciudad)", language="cypher")
                
        c3, c4 = st.columns([0.85, 0.15])
        with c3:
            st.metric("Edad", data['edad'])
        with c4:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.popover("🔍 Query"):
                st.code(f"MATCH (u:Usuario {{nombre: '{u_sel}'}}) RETURN u (Edad)", language="cypher")
        
        c5, c6 = st.columns([0.85, 0.15])
        with c5:
            st.write("### 📚 Intereses Especializados")
        with c6:
            with st.popover("🔍 Query"):
                st.code(f"MATCH (u:Usuario {{nombre: '{u_sel}'}})-[:INTERESADO_EN]->(t) RETURN t.nombre as t", language="cypher")
                
        intereses = [r['t'] for r in run_query("MATCH (u:Usuario {nombre: $n})-[:INTERESADO_EN]->(t) RETURN t.nombre as t", {"n": u_sel})]
        st.write(", ".join(intereses) if intereses else "Sin intereses definidos")

    with col2:
        c7, c8 = st.columns([0.85, 0.15])
        with c7:
            st.write("### 👥 Conexiones Directas")
        with c8:
            with st.popover("🔍 Query"):
                st.code(f"MATCH (u:Usuario {{nombre: '{u_sel}'}})-[:SIGUE]->(s) RETURN s.nombre as n", language="cypher")
                
        seguidos = run_query("MATCH (u:Usuario {nombre: $n})-[:SIGUE]->(s) RETURN s.nombre as n", {"n": u_sel})
        if seguidos:
            for s in seguidos: 
                st.text(f"➡️ Sigue a: {s['n']}")
        else:
            st.write("Sin conexiones")


elif menu == "🛠️ Gestión de Comunidad":
    st.header("Administración de Entidades")
    tab1, tab2 = st.tabs(["👥 Usuarios", "🏷️ Intereses"])    

    with tab1:
        st.subheader("➕ Alta")

        usuarios_existentes = [r['n'] for r in run_query("MATCH (u:Usuario) RETURN u.nombre AS n ORDER BY n")]
        temas_disponibles = [r['t'] for r in run_query("MATCH (t:Tema) RETURN t.nombre AS t ORDER BY t")]

        with st.form("nuevo_usuario"):
            nombre = st.text_input("Nombre completo (Único):")
            ciudad = st.selectbox("Ciudad:", ["Sevilla", "Madrid", "Barcelona", "Bilbao", "Valencia", "Málaga"])
            edad = st.slider("Edad:", 18, 70, 25)
            
            intereses_sel = st.multiselect("Temas de interés:", temas_disponibles)
            conexiones_sel = st.multiselect("Seguir a profesionales existentes:", usuarios_existentes)
            
            submit = st.form_submit_button("Dar de Alta y Conectar")
            
            if submit:
                nombre_limpio = nombre.strip()
                if not nombre_limpio:
                    st.error("El nombre no puede estar vacío.")
                elif any(u.lower() == nombre_limpio.lower() for u in usuarios_existentes):
                    st.error(f"El usuario '{nombre_limpio}' ya existe en la red. Elige otro nombre.")
                else:
                    run_query("CREATE (:Usuario {nombre: $n, ciudad: $c, edad: $e})", 
                            {"n": nombre_limpio, "c": ciudad, "e": edad})
                    
                    if intereses_sel:
                        run_query("MATCH (u:Usuario {nombre: $n}), (t:Tema) WHERE t.nombre IN $temas MERGE (u)-[:INTERESADO_EN]->(t)",
                                {"n": nombre_limpio, "temas": intereses_sel})
                    
                    if conexiones_sel:
                        run_query("MATCH (u:Usuario {nombre: $n}), (dest:Usuario) WHERE dest.nombre IN $conexiones MERGE (u)-[:SIGUE]->(dest)",
                                {"n": nombre_limpio, "conexiones": conexiones_sel})
                    
                    st.success(f"¡Bienvenido, {nombre_limpio}! Perfil creado y vinculado con {len(intereses_sel)} intereses.")
                    st.info("Query ejecutada:")
                    st.code(f"CREATE (:Usuario {{nombre: '{nombre_limpio}', ciudad: '{ciudad}', edad: {edad}}})", language="cypher")
                    if intereses_sel: st.code(f"MATCH (u:Usuario {{nombre: '{nombre_limpio}'}}), (t:Tema) WHERE t.nombre IN {intereses_sel} MERGE (u)-[:INTERESADO_EN]->(t)", language="cypher")
                    if conexiones_sel: st.code(f"MATCH (u:Usuario {{nombre: '{nombre_limpio}'}}), (dest:Usuario) WHERE dest.nombre IN {conexiones_sel} MERGE (u)-[:SIGUE]->(dest)", language="cypher")

        st.divider()
        st.subheader("🗑️ Baja")

        usuarios_eliminar = [r['n'] for r in run_query("MATCH (u:Usuario) RETURN u.nombre AS n ORDER BY n")]
        u_a_borrar = st.selectbox("Selecciona el perfil a eliminar de la red:", ["---"] + usuarios_eliminar)

        if u_a_borrar != "---":
            with st.form("Confirmar eliminación"):
                st.write(f"⚠️ Estás a punto de borrar a **{u_a_borrar}**. Esta acción es irreversible.")
                
                confirmar_borrado = st.checkbox(f"Confirmo que deseo eliminar permanentemente a {u_a_borrar}")
                
                submit = st.form_submit_button("Ejecutar Borrado")
                if submit:
                    if not confirmar_borrado:
                        st.error("Debes marcar la casilla de confirmación para proceder.")
                    else:
                        run_query("MATCH (u:Usuario {nombre: $n}) DETACH DELETE u", {"n": u_a_borrar})
                        st.success(f"El usuario {u_a_borrar} ha sido eliminado satisfactoriamente.")
                        st.info("Query ejecutada:")
                        st.code(f"MATCH (u:Usuario {{nombre: '{u_a_borrar}'}}) DETACH DELETE u", language="cypher")
        
        st.divider()
        st.subheader("📝 Edición")
        
        usuarios_lista = [r['n'] for r in run_query("MATCH (u:Usuario) RETURN u.nombre AS n ORDER BY n")]
        u_editar = st.selectbox("Selecciona el perfil a modificar:", ["---"] + usuarios_lista, key="edit_full")
        
        if u_editar != "---":
            cur_temas = [r['t'] for r in run_query(
                "MATCH (u:Usuario {nombre: $n})-[:INTERESADO_EN]->(t:Tema) RETURN t.nombre AS t", {"n": u_editar})]
            cur_seguidos = [r['s'] for r in run_query(
                "MATCH (u:Usuario {nombre: $n})-[:SIGUE]->(s:Usuario) RETURN s.nombre AS s", {"n": u_editar})]
            
            dispo_temas = [r['t'] for r in run_query(
                "MATCH (t:Tema) WHERE NOT t.nombre IN $cur RETURN t.nombre AS t", {"cur": cur_temas})]
            dispo_seguidos = [r['s'] for r in run_query(
                "MATCH (s:Usuario) WHERE s.nombre <> $n AND NOT s.nombre IN $cur RETURN s.nombre AS s", 
                {"n": u_editar, "cur": cur_seguidos})]

            with st.form("form_edicion_completa"):
                st.info(f"Gestionando conexiones de: **{u_editar}**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("### ➕ Añadir")
                    add_t = st.multiselect("Nuevos Temas:", dispo_temas)
                    add_s = st.multiselect("Nuevos Seguidos:", dispo_seguidos)
                    
                with col2:
                    st.write("### ➖ Eliminar")
                    del_t = st.multiselect("Quitar Temas actuales:", cur_temas)
                    del_s = st.multiselect("Dejar de seguir a:", cur_seguidos)
                
                submit = st.form_submit_button("Actualizar Perfil")
                
                if submit:
                    if add_t:
                        run_query("MATCH (u:Usuario {nombre:$n}), (t:Tema) WHERE t.nombre IN $temas MERGE (u)-[:INTERESADO_EN]->(t)", {"n":u_editar, "temas":add_t})
                    if add_s:
                        run_query("MATCH (u:Usuario {nombre:$n}), (s:Usuario) WHERE s.nombre IN $seguidos MERGE (u)-[:SIGUE]->(s)", {"n":u_editar, "seguidos":add_s})
                    
                    if del_t:
                        run_query("MATCH (u:Usuario {nombre:$n})-[r:INTERESADO_EN]->(t:Tema) WHERE t.nombre IN $temas DELETE r", {"n":u_editar, "temas":del_t})
                    if del_s:
                        run_query("MATCH (u:Usuario {nombre:$n})-[r:SIGUE]->(s:Usuario) WHERE s.nombre IN $seguidos DELETE r", {"n":u_editar, "seguidos":del_s})
                    
                    st.success(f"Actualización completada para {u_editar}.")
                    st.info("Queries ejecutadas:")
                    if add_t: st.code(f"MATCH (u:Usuario {{nombre: '{u_editar}'}}), (t:Tema) WHERE t.nombre IN {add_t} MERGE (u)-[:INTERESADO_EN]->(t)", language="cypher")
                    if add_s: st.code(f"MATCH (u:Usuario {{nombre: '{u_editar}'}}), (s:Usuario) WHERE s.nombre IN {add_s} MERGE (u)-[:SIGUE]->(s)", language="cypher")
                    if del_t: st.code(f"MATCH (u:Usuario {{nombre: '{u_editar}'}})-[r:INTERESADO_EN]->(t:Tema) WHERE t.nombre IN {del_t} DELETE r", language="cypher")
                    if del_s: st.code(f"MATCH (u:Usuario {{nombre: '{u_editar}'}})-[r:SIGUE]->(s:Usuario) WHERE s.nombre IN {del_s} DELETE r", language="cypher")

    with tab2:
        st.subheader("Gestión de Temas de la Asignatura")
        col_c, col_b = st.columns(2)
        
        with col_c:
            st.write("### 🆕 Crear")
            nuevo_tema = st.text_input("Nombre del nuevo tema:", placeholder="Ej. Deep Learning")
            
            if st.button("Registrar Tema"):
                tema_limpio = nuevo_tema.strip()
                temas_lista = [r['t'] for r in run_query("MATCH (t:Tema) RETURN t.nombre AS t ORDER BY t")]
                
                if not tema_limpio:
                    st.error("⚠️ Error: El nombre del tema no puede estar vacío.")
                elif any(t.lower() == tema_limpio.lower() for t in temas_lista):
                    st.error(f"⚠️ Error: El tema '{tema_limpio}' ya existe.")
                else:
                    run_query("MERGE (:Tema {nombre: $t})", {"t": tema_limpio})
                    st.success(f"✅ Tema '{tema_limpio}' añadido con éxito.")
                    st.info("Query ejecutada:")
                    st.code(f"MERGE (:Tema {{nombre: '{tema_limpio}'}})", language="cypher")

        with col_b:
            st.write("### 🗑️ Eliminar")
            temas_lista = [r['t'] for r in run_query("MATCH (t:Tema) RETURN t.nombre AS t ORDER BY t")]
            tema_borrar = st.selectbox("Selecciona un tema para suprimir:", ["---"] + temas_lista)
            
            if st.button("Confirmar Eliminación de Tema"):
                if tema_borrar != "---":
                    run_query("MATCH (t:Tema {nombre: $t}) DETACH DELETE t", {"t": tema_borrar})
                    st.success(f"El tema '{tema_borrar}' ha sido eliminado del sistema.")
                    st.info("Query ejecutada:")
                    st.code(f"MATCH (t:Tema {{nombre: '{tema_borrar}'}}) DETACH DELETE t", language="cypher")
                else:
                    st.warning("Para eliminar un tema primero debes seleccionar uno de la lista.")


elif menu == "🧠 Inteligencia de Red":
    st.header("Analítica Avanzada de Grafos")
    st.write("Algoritmos predefinidos para análisis de datos.")
    
    if st.button("🏆 Identificar Líderes de Opinión"):
        res = run_query("MATCH (u:Usuario)<-[:SIGUE]-(seguidor) RETURN u.nombre as n, count(seguidor) as c ORDER BY c DESC LIMIT 5")
        for r in res: st.write(f"**{r['n']}** es seguido por {r['c']} profesionales.")
        st.info("Query ejecutada:")
        st.code("MATCH (u:Usuario)<-[:SIGUE]-(seguidor) RETURN u.nombre as n, count(seguidor) as c ORDER BY c DESC LIMIT 5", language="cypher")
    st.divider()
    st.write("### 🔗 Localizador de Rutas (Grados de Separación)")
    
    usuarios_lista = [r['n'] for r in run_query("MATCH (u:Usuario) RETURN u.nombre AS n ORDER BY n")]
    u1 = st.selectbox("Origen:", usuarios_lista, key="u1")
    
    usuarios_destino = [u for u in usuarios_lista if u != u1]
    u2 = st.selectbox("Destino:", usuarios_destino, key="u2")
    
    if st.button("Calcular ruta óptima"):
        if u1 == u2:
            st.error("Origen y destino no pueden ser el mismo.")
        else:
            query = """
            MATCH p = shortestPath((a:Usuario {nombre:$n1})-[:SIGUE*..6]-(b:Usuario {nombre:$n2}))
            RETURN [n in nodes(p) | n.nombre] AS nombres
            """
            res = run_query(query, {"n1": u1, "n2": u2})
            
            if res and res[0]['nombres']:
                ruta = res[0]['nombres']
                st.write("#### 📍 Ruta encontrada:")
                st.subheader(" ➡️ ".join(ruta))
                st.info(f"La conexión se establece a través de {len(ruta)-2} intermediarios.")
            else:
                st.error("No existe una ruta de conexión entre estos dos perfiles en el grafo actual.")
            
            st.info("Query ejecutada:")
            query_str = f"MATCH p = shortestPath((a:Usuario {{nombre: '{u1}'}})-[:SIGUE*..6]-(b:Usuario {{nombre: '{u2}'}}))\nRETURN [n in nodes(p) | n.nombre] AS nombres"
            st.code(query_str, language="cypher")

    st.divider()
    st.write("### 🔍 Filtrado Dinámico de Intereses")
    st.write("Encuentra grupos de profesionales especializados en áreas concretas.")

    temas_disponibles = [r['t'] for r in run_query("MATCH (t:Tema) RETURN t.nombre AS t ORDER BY t")]
    
    temas_busqueda = st.multiselect("Filtrar red por conocimientos:", temas_disponibles)

    if temas_busqueda:
        query_filtro = """
        MATCH (u:Usuario)-[:INTERESADO_EN]->(t:Tema)
        WHERE t.nombre IN $temas
        RETURN u.nombre AS nombre, u.ciudad AS ciudad, count(t) AS coincidencia
        ORDER BY coincidencia DESC, u.nombre ASC
        """
        resultados = run_query(query_filtro, {"temas": temas_busqueda})

        if resultados:
            st.success(f"Se han encontrado {len(resultados)} usuarios interesados en: {', '.join(temas_busqueda)}")
            
            for res in resultados:
                st.write(f"👤 **{res['nombre']}** ({res['ciudad']}) - Coincide en {res['coincidencia']} tema(s).")
            
            with st.expander("🔍 Ver query usada"):
                st.code(f"""
                MATCH (u:Usuario)-[:INTERESADO_EN]->(t:Tema)
                WHERE t.nombre IN {temas_busqueda}
                RETURN u.nombre, u.ciudad, count(t) AS coincidencia
                ORDER BY coincidencia DESC
                """, language="cypher")
        else:
            st.warning("No hay usuarios registrados con esa combinación de intereses.")
