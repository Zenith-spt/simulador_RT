import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Simposio 100m - Tiempo de Reacción", page_icon="⏱️", layout="centered")

# Almacenamiento compartido entre todos los móviles conectados a la sesión
@st.cache_resource
def obtener_base_datos():
    return []

db_global = obtener_base_datos()

st.title("⏱️ Simposio 100m: Tiempo de Reacción")
st.caption("Práctica experimental: Estímulo Visual vs. Estímulo Auditivo")

# Pestañas: una para que los alumnos hagan el test y otra para proyectar en clase
tab_test, tab_resultados = st.tabs(["📱 Realizar Test (Móvil)", "📊 Resultados del Simposio (Proyector)"])

with tab_test:
    col_nombre, col_mod = st.columns([1, 1])
    with col_nombre:
        participante = st.text_input("Tu nombre o alias:", value="Atleta", max_chars=20)
    with col_mod:
        modalidad = st.selectbox("Modalidad de estímulo:", ["Auditivo (Disparo 1000Hz)", "Visual (Luz Verde)"])

    es_auditivo = "Auditivo" in modalidad

    # Componente de precisión local en el móvil (0 ms de latencia de red)
    # Utiliza Web Audio API para generar el disparo sin retrasos de carga
    html_test = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 0; display: flex; flex-direction: column; align-items: center;
            user-select: none; -webkit-user-select: none;
        }}
        #zona-tactil {{
            width: 100%; height: 260px; border-radius: 16px;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            text-align: center; color: white; font-weight: bold; cursor: pointer;
            transition: background-color 0.05s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            touch-action: manipulation;
        }}
        .estado-inicio {{ background-color: #2b5c8f; }}
        .estado-espera {{ background-color: #d97706; }}
        .estado-estimulo-visual {{ background-color: #16a34a; }}
        .estado-estimulo-auditivo {{ background-color: #1e293b; border: 4px solid #ef4444; }}
        .estado-nula {{ background-color: #dc2626; }}
        .estado-fin {{ background-color: #0284c7; }}
        h2 {{ font-size: 26px; margin: 0 15px; }}
        p {{ font-size: 16px; margin-top: 10px; opacity: 0.9; padding: 0 20px; }}
    </style>
    </head>
    <body>
        <div id="zona-tactil" class="estado-inicio" onpointerdown="manejarToque()">
            <h2 id="titulo">TOCA PARA PREPARARTE</h2>
            <p id="subtitulo">Mantén la atención. Reacciona al instante cuando aparezca la señal.</p>
        </div>

        <script>
            let estado = 'inicio'; // inicio, esperando, estimulo, fin
            let tiempoInicio = 0;
            let timerId = null;
            let audioCtx = null;
            const esAuditivo = {str(es_auditivo).lower()};

            function inicializarAudio() {{
                if (!audioCtx) {{
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                }}
                if (audioCtx.state === 'suspended') {{
                    audioCtx.resume();
                }}
            }}

            function dispararSonido() {{
                if (!audioCtx) return;
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sawtooth'; // Timbre agudo tipo pistola electrónica
                osc.frequency.setValueAtTime(1000, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.8, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.15);
            }}

            function manejarToque() {{
                const caja = document.getElementById('zona-tactil');
                const titulo = document.getElementById('titulo');
                const subtitulo = document.getElementById('subtitulo');

                if (estado === 'inicio' || estado === 'fin') {{
                    // Desbloquear audio del móvil en el primer toque del usuario
                    inicializarAudio();
                    estado = 'esperando';
                    caja.className = 'estado-espera';
                    titulo.innerText = '🟡 LISTOS...';
                    subtitulo.innerText = esAuditivo ? 'Escucha atentamente el disparo...' : 'Espera al cambio a color VERDE...';

                    // Tiempo aleatorio oficial entre 1.5s y 3.8s
                    const espera = Math.floor(Math.random() * 2300) + 1500;
                    timerId = setTimeout(() => {{
                        estado = 'estimulo';
                        if (esAuditivo) {{
                            dispararSonido();
                            caja.className = 'estado-estimulo-auditivo';
                            titulo.innerText = '🔊 ¡DISPARO!';
                            subtitulo.innerText = '¡TOCA AHORA!';
                        }} else {{
                            caja.className = 'estado-estimulo-visual';
                            titulo.innerText = '🟢 ¡YA!';
                            subtitulo.innerText = '¡TOCA AHORA!';
                        }}
                        tiempoInicio = performance.now();
                    }}, espera);

                }} else if (estado === 'esperando') {{
                    clearTimeout(timerId);
                    estado = 'fin';
                    caja.className = 'estado-nula';
                    titulo.innerText = '🚫 ¡SALIDA NULA!';
                    subtitulo.innerText = 'Te has adelantado al estímulo. Toca para repetir.';

                }} else if (estado === 'estimulo') {{
                    const tiempoFin = performance.now();
                    const tr = (tiempoFin - tiempoInicio).toFixed(1);
                    estado = 'fin';
                    caja.className = 'estado-fin';
                    titulo.innerText = tr + ' ms';
                    
                    let feedback = '';
                    if (tr < 100) feedback = '⚠️ <100 ms: Salida nula por regla World Athletics';
                    else if (tr <= 165) feedback = '🏆 Rango finalista olímpico 100m (120-165 ms)';
                    else if (tr <= 230) feedback = '🏃 Rango velocista entrenado / activo';
                    else feedback = '⏱️ Toca para intentar mejorar tu marca';

                    subtitulo.innerText = feedback + ' (Registra tu marca abajo)';
                }}
            }}
        </script>
    </body>
    </html>
    """

    components.html(html_test, height=275)

    # Formulario rápido para enviar el dato al proyector del aula
    with st.form("registro_dato", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            valor_ms = st.number_input("Introduce tu marca obtenida (ms):", min_value=50.0, max_value=1000.0, step=0.1, value=160.0)
        with c2:
            st.write("") # Espaciador visual
            enviado = st.form_submit_button("📤 Enviar al Simposio", use_container_width=True, type="primary")
        
        if enviado:
            db_global.append({
                "Participante": participante,
                "Estímulo": "Auditivo" if es_auditivo else "Visual",
                "Tiempo (ms)": round(valor_ms, 1)
            })
            st.success(f"¡Marca de **{valor_ms} ms** ({'Auditivo' if es_auditivo else 'Visual'}) enviada a la pantalla principal!")

with tab_resultados:
    st.subheader("Análisis Comparativo en Tiempo Real")
    
    if not db_global:
        st.info("Aún no hay registros. Pide a los alumnos que realicen el test y envíen sus tiempos.")
    else:
        df = pd.DataFrame(db_global)
        
        auditivos = df[df["Estímulo"] == "Auditivo"]["Tiempo (ms)"]
        visuales = df[df["Estímulo"] == "Visual"]["Tiempo (ms)"]

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Intentos", len(df))
        m2.metric("Media Auditiva (Disparo)", f"{auditivos.mean():.1f} ms" if not auditivos.empty else "-")
        m3.metric("Media Visual (Luz)", f"{visuales.mean():.1f} ms" if not visuales.empty else "-")

        # Diferencia fisiológica esperada (Auditivo suele ser ~30-50 ms más rápido que Visual)
        if not auditivos.empty and not visuales.empty:
            diff = visuales.mean() - auditivos.mean()
            st.info(f"💡 **Diferencia observada en el aula:** El estímulo auditivo está siendo **{diff:.1f} ms** más rápido que el visual (en literatura científica la vía auditiva tarda ~8-10 ms en llegar al córtex frente a ~20-40 ms de la vía visual).")

        st.bar_chart(df.groupby("Estímulo")["Tiempo (ms)"].mean(), y_label="Tiempo medio (ms)")
        
        with st.expander("Ver tabla completa de registros y ranking"):
            st.dataframe(df.sort_values(by="Tiempo (ms)"), use_container_width=True)
            if st.button("🗑️ Reiniciar datos del simposio"):
                db_global.clear()
                st.rerun()
        st.rerun()