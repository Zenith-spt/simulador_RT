from datetime import datetime
import io
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Simposio 100m - Tiempo de Reacción", page_icon="⏱️", layout="centered")


# Almacenamiento global sincronizado entre todos los dispositivos conectados
@st.cache_resource
def obtener_base_datos():
    return []


db_global = obtener_base_datos()

if "ultimo_id_enviado" not in st.session_state:
    st.session_state.ultimo_id_enviado = None

st.title("⏱️ Simposio 100m: Tiempo de Reacción")
st.caption("Práctica experimental: Estímulo Auditivo vs. Estímulo Visual")

tab_test, tab_ranking = st.tabs(["📱 Realizar Prueba (Móvil)", "🏆 Rankings y Hoja de Cálculo"])

# ==============================================================================
# PESTAÑA 1: PRUEBA EN EL MÓVIL (CAPTURA AUTOMÁTICA)
# ==============================================================================
with tab_test:
    c1, c2 = st.columns(2)
    with c1:
        participante = st.text_input("Tu nombre o alias:", placeholder="Ej. Ana G.", max_chars=25)
    with c2:
        modalidad = st.selectbox("Modalidad:", ["Auditivo (Disparo 1000Hz)", "Visual (Luz Verde)"])

    es_auditivo = "Auditivo" in modalidad

    html_test = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 0;
            user-select: none; -webkit-user-select: none;
            background: transparent;
        }}
        #zona-tactil {{
            width: 100%; height: 245px; border-radius: 16px;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            text-align: center; color: white; font-weight: bold;
            cursor: pointer; touch-action: manipulation;
            background-color: #2b5c8f;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 16px;
            transition: background-color 0.05s;
        }}
        #titulo {{ font-size: 24px; line-height: 1.2; }}
        #sub {{ font-size: 15px; margin-top: 10px; opacity: 0.92; line-height: 1.3; }}
    </style>
    </head>
    <body>
        <div id="zona-tactil">
            <div id="titulo">TOCA PARA PREPARARTE</div>
            <div id="sub">Reacciona en cuanto percibas la señal.</div>
        </div>

        <script>
            const box = document.getElementById('zona-tactil');
            const titulo = document.getElementById('titulo');
            const sub = document.getElementById('sub');

            let estado = 'inicio'; // inicio, esperando, estimulo, fin
            let tInicio = 0;
            let timer = null;
            let audioCtx = null;
            const esAuditivo = {str(es_auditivo).lower()};

            function initAudio() {{
                if (!audioCtx) {{
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    if (AudioContext) audioCtx = new AudioContext();
                }}
                if (audioCtx && audioCtx.state === 'suspended') {{
                    audioCtx.resume();
                }}
            }}

            function beep() {{
                if (!audioCtx) return;
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(1000, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.8, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.15);
            }}

            function enviarMarcaAPython(ms, tipo) {{
                const idUnico = Date.now() + "_" + Math.floor(Math.random() * 10000);
                try {{
                    const parentUrl = new URL(window.parent.location.href);
                    parentUrl.searchParams.set('tr_ms', ms);
                    parentUrl.searchParams.set('tr_tipo', tipo);
                    parentUrl.searchParams.set('tr_id', idUnico);
                    window.parent.history.replaceState({{}}, '', parentUrl.toString());
                    // Notificar a Streamlit del cambio en la URL
                    window.parent.dispatchEvent(new PopStateEvent('popstate'));
                }} catch (e) {{
                    console.log("No se pudo actualizar URL padre:", e);
                }}
            }}

            box.addEventListener('pointerdown', (e) => {{
                e.preventDefault();

                if (estado === 'inicio' || estado === 'fin') {{
                    initAudio();
                    estado = 'esperando';
                    box.style.backgroundColor = '#d97706';
                    box.style.border = 'none';
                    titulo.innerText = '🟡 LISTOS...';
                    sub.innerText = esAuditivo ? 'Atento al disparo...' : 'Atento al color VERDE...';

                    const espera = Math.floor(Math.random() * 2300) + 1500;
                    timer = setTimeout(() => {{
                        estado = 'estimulo';
                        if (esAuditivo) {{
                            beep();
                            box.style.backgroundColor = '#1e293b';
                            box.style.border = '4px solid #ef4444';
                            titulo.innerText = '🔊 ¡DISPARO!';
                            sub.innerText = '¡TOCA AHORA!';
                        }} else {{
                            box.style.backgroundColor = '#16a34a';
                            box.style.border = 'none';
                            titulo.innerText = '🟢 ¡YA!';
                            sub.innerText = '¡TOCA AHORA!';
                        }}
                        tInicio = performance.now();
                    }}, espera);

                }} else if (estado === 'esperando') {{
                    clearTimeout(timer);
                    estado = 'fin';
                    box.style.backgroundColor = '#dc2626';
                    box.style.border = 'none';
                    titulo.innerText = '🚫 ¡SALIDA NULA!';
                    sub.innerText = 'Te has adelantado. Toca aquí para repetir.';

                }} else if (estado === 'estimulo') {{
                    const tr = Number((performance.now() - tInicio).toFixed(1));
                    estado = 'fin';
                    box.style.backgroundColor = '#0284c7';
                    box.style.border = 'none';
                    titulo.innerText = tr + ' ms';
                    sub.innerText = 'Marca capturada. Pulsa el botón de abajo para enviarla o toca aquí para repetir.';
                    enviarMarcaAPython(tr, esAuditivo ? 'Auditivo' : 'Visual');
                }}
            }});
        </script>
    </body>
    </html>
    """

    components.html(html_test, height=265)

    # Leer marca capturada automáticamente desde los parámetros de la URL
    tr_ms_param = st.query_params.get("tr_ms")
    tr_tipo_param = st.query_params.get("tr_tipo")
    tr_id_param = st.query_params.get("tr_id")

    if tr_ms_param and tr_tipo_param and tr_id_param:
        try:
            ms_val = round(float(tr_ms_param), 1)
            ya_enviada = st.session_state.ultimo_id_enviado == tr_id_param

            st.divider()
            col_info, col_btn = st.columns([1.3, 1])
            with col_info:
                st.markdown(f"**Última marca detectada:** `{ms_val} ms` ({tr_tipo_param})")
                if ms_val < 100:
                    st.caption("⚠️ *Nota: < 100 ms se considera salida nula en World Athletics.*")
            with col_btn:
                if not ya_enviada:
                    if st.button(f"📤 Enviar {ms_val} ms", type="primary", use_container_width=True):
                        nombre_final = participante.strip() if participante.strip() else "Anónimo"
                        db_global.append({
                            "Hora": datetime.now().strftime("%H:%M:%S"),
                            "Participante": nombre_final,
                            "Prueba": tr_tipo_param,
                            "Tiempo (ms)": ms_val,
                        })
                        st.session_state.ultimo_id_enviado = tr_id_param
                        st.success("✅ ¡Marca registrada en el ranking!")
                        st.rerun()
                else:
                    st.button("✔️ Marca enviada", disabled=True, use_container_width=True)
        except ValueError:
            pass

# ==============================================================================
# PESTAÑA 2: RANKINGS SEPARADOS Y EXPORTACIÓN A HOJA DE CÁLCULO
# ==============================================================================
with tab_ranking:
    col_t, col_ref = st.columns([3, 1])
    with col_t:
        st.subheader("Clasificación en Tiempo Real")
    with col_ref:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()

    if not db_global:
        st.info("Esperando resultados de los participantes...")
    else:
        df = pd.DataFrame(db_global)

        df_aud = df[df["Prueba"] == "Auditivo"].sort_values(by="Tiempo (ms)").reset_index(drop=True)
        df_vis = df[df["Prueba"] == "Visual"].sort_values(by="Tiempo (ms)").reset_index(drop=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Participaciones", len(df))
        m2.metric("Media Auditiva", f"{df_aud['Tiempo (ms)'].mean():.1f} ms" if not df_aud.empty else "-")
        m3.metric("Media Visual", f"{df_vis['Tiempo (ms)'].mean():.1f} ms" if not df_vis.empty else "-")

        st.divider()

        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown("### 🔊 Ranking Auditivo")
            if df_aud.empty:
                st.caption("Sin registros auditivos aún.")
            else:
                df_aud.index = df_aud.index + 1
                st.dataframe(df_aud[["Participante", "Tiempo (ms)"]], use_container_width=True)

        with col_r2:
            st.markdown("### 🟢 Ranking Visual")
            if df_vis.empty:
                st.caption("Sin registros visuales aún.")
            else:
                df_vis.index = df_vis.index + 1
                st.dataframe(df_vis[["Participante", "Tiempo (ms)"]], use_container_width=True)

        st.divider()

        st.markdown("### 📥 Exportar a Hoja de Cálculo")
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Todos_los_datos", index=False)
            if not df_aud.empty:
                df_aud.to_excel(writer, sheet_name="Ranking_Auditivo", index_label="Posición")
            if not df_vis.empty:
                df_vis.to_excel(writer, sheet_name="Ranking_Visual", index_label="Posición")

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📊 Descargar Excel (.xlsx)",
                data=buffer_excel.getvalue(),
                file_name=f"Resultados_Simposio_100m_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
        with col_dl2:
            if st.button("🗑️ Limpiar todos los datos", use_container_width=True):
                db_global.clear()
                st.rerun()
