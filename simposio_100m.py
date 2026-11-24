from datetime import datetime
import io
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Simposio tiempo de reacción", page_icon="⏱️", layout="centered")

# PIN de seguridad para acciones de gestión
try:
    PIN_ORGANIZADOR = st.secrets["pin_organizador"]
except Exception:
    PIN_ORGANIZADOR = "100m"


# Almacenamiento global sincronizado entre todos los dispositivos conectados
@st.cache_resource
def obtener_base_datos():
    return []


db_global = obtener_base_datos()

# Estados locales independientes por cada usuario/dispositivo
if "historial_personal" not in st.session_state:
    st.session_state.historial_personal = []
if "ultimo_id_enviado" not in st.session_state:
    st.session_state.ultimo_id_enviado = None
if "modo_organizador" not in st.session_state:
    st.session_state.modo_organizador = False

st.title("Simposio tiempo de reacción")
st.caption("Práctica experimental: Tiempo de reacción auditivo y visual")

tab_test, tab_personal, tab_ranking = st.tabs([
    "📱 Realizar Prueba",
    "📈 Informe Personal",
    "🏆 Rankings y Hoja de Cálculo",
])

# ==============================================================================
# PANTALLA 1: REALIZAR PRUEBA (MÓVIL)
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
                if (audioCtx) {{
                    if (audioCtx.state === 'suspended') {{
                        audioCtx.resume();
                    }}
                    try {{
                        const buffer = audioCtx.createBuffer(1, 1, 22050);
                        const source = audioCtx.createBufferSource();
                        source.buffer = buffer;
                        source.connect(audioCtx.destination);
                        source.start(0);
                    }} catch (e) {{}}
                }}
            }}

            function beep() {{
                initAudio();
                if (!audioCtx) return;

                const ahora = audioCtx.currentTime;
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();

                osc.type = 'square';
                osc.frequency.setValueAtTime(1000, ahora);

                gain.gain.setValueAtTime(0.001, ahora);
                gain.gain.exponentialRampToValueAtTime(0.9, ahora + 0.01);
                gain.gain.exponentialRampToValueAtTime(0.001, ahora + 0.22);

                osc.connect(gain);
                gain.connect(audioCtx.destination);

                osc.start(ahora);
                osc.stop(ahora + 0.23);
            }}

            function enviarMarcaAPython(ms, tipo) {{
                const idUnico = Date.now() + "_" + Math.floor(Math.random() * 10000);
                try {{
                    const parentUrl = new URL(window.parent.location.href);
                    parentUrl.searchParams.set('tr_ms', ms);
                    parentUrl.searchParams.set('tr_tipo', tipo);
                    parentUrl.searchParams.set('tr_id', idUnico);
                    window.parent.history.replaceState({{}}, '', parentUrl.toString());
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
                        tInicio = performance.now();
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
                    sub.innerText = 'Marca capturada. Pulsa el botón de abajo para registrarla o toca aquí para repetir.';
                    enviarMarcaAPython(tr, esAuditivo ? 'Auditivo' : 'Visual');
                }}
            }});
        </script>
    </body>
    </html>
    """

    components.html(html_test, height=265)

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
                    if st.button(f"📤 Registrar {ms_val} ms", type="primary", use_container_width=True):
                        nombre_final = participante.strip() if participante.strip() else "Anónimo"
                        registro = {
                            "Intento": len(st.session_state.historial_personal) + 1,
                            "Hora": datetime.now().strftime("%H:%M:%S"),
                            "Participante": nombre_final,
                            "Prueba": tr_tipo_param,
                            "Tiempo (ms)": ms_val,
                            "Válido (>=100ms)": "Sí" if ms_val >= 100 else "No (Anticipación)",
                        }
                        st.session_state.historial_personal.append(registro)
                        db_global.append(registro)
                        st.session_state.ultimo_id_enviado = tr_id_param
                        st.success("✅ ¡Marca guardada en tu informe y enviada al ranking!")
                        st.rerun()
                else:
                    st.button("✔️ Marca registrada", disabled=True, use_container_width=True)
        except ValueError:
            pass

# ==============================================================================
# PANTALLA 2: INFORME PERSONAL Y ANÁLISIS DESCRIPTIVO BÁSICO
# ==============================================================================
with tab_personal:
    st.subheader("📈 Tu Informe Individual de Rendimiento")

    if not st.session_state.historial_personal:
        st.info("Aún no has registrado ninguna marca. Realiza al menos una prueba en la primera pestaña.")
    else:
        df_ind = pd.DataFrame(st.session_state.historial_personal)
        nombre_usuario = df_ind["Participante"].iloc[-1]
        st.markdown(f"**Participante:** `{nombre_usuario}` | **Total de intentos registrados:** `{len(df_ind)}`")

        df_ind_val = df_ind[df_ind["Tiempo (ms)"] >= 100]
        aud_ind = df_ind_val[df_ind_val["Prueba"] == "Auditivo"]["Tiempo (ms)"]
        vis_ind = df_ind_val[df_ind_val["Prueba"] == "Visual"]["Tiempo (ms)"]

        st.markdown("### 📊 Análisis Descriptivo Básico (Intentos válidos ≥ 100 ms)")

        def calcular_descriptivos(serie):
            if serie.empty:
                return ["-", "-", "-", "-", "-", "-", 0]
            media = f"{serie.mean():.1f}"
            de = f"{serie.std():.1f}" if len(serie) > 1 else "0.0"
            mediana = f"{serie.median():.1f}"
            mejor = f"{serie.min():.1f}"
            peor = f"{serie.max():.1f}"
            rango = f"{(serie.max() - serie.min()):.1f}"
            n = len(serie)
            return [n, media, de, mediana, mejor, peor, rango]

        tabla_desc = pd.DataFrame({
            "Estadístico": [
                "N (Intentos válidos)",
                "Media (ms)",
                "Desviación Estándar (ms)",
                "Mediana (ms)",
                "Mejor Marca / Mínimo (ms)",
                "Peor Marca / Máximo (ms)",
                "Rango (ms)",
            ],
            "🔊 Auditivo": calcular_descriptivos(aud_ind),
            "🟢 Visual": calcular_descriptivos(vis_ind),
        })

        st.dataframe(tabla_desc, hide_index=True, use_container_width=True)

        if not aud_ind.empty and not vis_ind.empty:
            diff_ind = vis_ind.mean() - aud_ind.mean()
            if diff_ind > 0:
                st.success(
                    f"💡 **Tu perfil fisiológico:** Tu tiempo de reacción auditivo medio es **{diff_ind:.1f} ms más rápido** que tu tiempo visual."
                )
            else:
                st.info(
                    f"💡 **Tu perfil fisiológico:** Tu tiempo visual medio ha sido **{abs(diff_ind):.1f} ms más rápido** que el auditivo en esta serie."
                )

        st.divider()

        st.markdown("### 📋 Registro Completo de Tus Intentos")
        st.dataframe(
            df_ind[["Intento", "Hora", "Prueba", "Tiempo (ms)", "Válido (>=100ms)"]],
            hide_index=True,
            use_container_width=True,
        )

        buffer_ind = io.BytesIO()
        with pd.ExcelWriter(buffer_ind, engine="openpyxl") as writer:
            tabla_desc.to_excel(writer, sheet_name="Analisis_Descriptivo", index=False)
            df_ind.to_excel(writer, sheet_name="Mis_Intentos", index=False)

        col_ind1, col_ind2 = st.columns(2)
        with col_ind1:
            st.download_button(
                label="📥 Descargar mi informe (.xlsx)",
                data=buffer_ind.getvalue(),
                file_name=f"Informe_TR_{nombre_usuario.replace(' ', '_')}_{datetime.now().strftime('%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
        with col_ind2:
            if st.button("🔄 Reiniciar mi historial personal", use_container_width=True):
                st.session_state.historial_personal = []
                st.rerun()

# ==============================================================================
# PANTALLA 3: RANKINGS (MEJOR MARCA POR SUJETO) Y HOJA DE CÁLCULO GLOBAL
# ==============================================================================
with tab_ranking:
    col_t, col_ref = st.columns([3, 1])
    with col_t:
        st.subheader("Clasificación General (Mejor Marca por Sujeto)")
    with col_ref:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()

    if not db_global:
        st.info("Esperando resultados de los participantes...")
    else:
        df = pd.DataFrame(db_global)

        df_validos = df[df["Tiempo (ms)"] >= 100].copy()

        if not df_validos[df_validos["Prueba"] == "Auditivo"].empty:
            df_aud_best = (
                df_validos[df_validos["Prueba"] == "Auditivo"]
                .groupby("Participante", as_index=False)["Tiempo (ms)"]
                .min()
                .sort_values(by="Tiempo (ms)")
                .reset_index(drop=True)
            )
        else:
            df_aud_best = pd.DataFrame(columns=["Participante", "Tiempo (ms)"])

        if not df_validos[df_validos["Prueba"] == "Visual"].empty:
            df_vis_best = (
                df_validos[df_validos["Prueba"] == "Visual"]
                .groupby("Participante", as_index=False)["Tiempo (ms)"]
                .min()
                .sort_values(by="Tiempo (ms)")
                .reset_index(drop=True)
            )
        else:
            df_vis_best = pd.DataFrame(columns=["Participante", "Tiempo (ms)"])

        m1, m2, m3 = st.columns(3)
        m1.metric("Sujetos únicos", df["Participante"].nunique())
        m2.metric("Media Mejores Auditivo", f"{df_aud_best['Tiempo (ms)'].mean():.1f} ms" if not df_aud_best.empty else "-")
        m3.metric("Media Mejores Visual", f"{df_vis_best['Tiempo (ms)'].mean():.1f} ms" if not df_vis_best.empty else "-")

        st.divider()

        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown("### 🔊 Ranking Auditivo")
            st.caption("Mejor marca válida (≥ 100 ms) por participante")
            if df_aud_best.empty:
                st.info("Sin registros válidos aún.")
            else:
                df_aud_best.index = df_aud_best.index + 1
                st.dataframe(df_aud_best, use_container_width=True)

        with col_r2:
            st.markdown("### 🟢 Ranking Visual")
            st.caption("Mejor marca válida (≥ 100 ms) por participante")
            if df_vis_best.empty:
                st.info("Sin registros válidos aún.")
            else:
                df_vis_best.index = df_vis_best.index + 1
                st.dataframe(df_vis_best, use_container_width=True)

        st.divider()

        st.markdown("### 📥 Exportar Base de Datos Global")
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Todos_los_intentos", index=False)
            if not df_aud_best.empty:
                df_aud_best.to_excel(writer, sheet_name="Ranking_Mejor_Auditivo", index_label="Posición")
            if not df_vis_best.empty:
                df_vis_best.to_excel(writer, sheet_name="Ranking_Mejor_Visual", index_label="Posición")

        st.download_button(
            label="📊 Descargar Excel General (.xlsx)",
            data=buffer_excel.getvalue(),
            file_name=f"Resultados_Simposio_TR_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )

        st.divider()

        with st.expander("🔒 Administración de datos (Solo organizador)"):
            if not st.session_state.modo_organizador:
                pin_introducido = st.text_input("Introduce el PIN de organizador:", type="password", key="pin_input")
                if st.button("🔓 Desbloquear gestión"):
                    if pin_introducido == PIN_ORGANIZADOR:
                        st.session_state.modo_organizador = True
                        st.rerun()
                    else:
                        st.error("PIN incorrecto.")
            else:
                st.success("Modo organizador activo.")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("🗑️ Limpiar base de datos global", type="primary", use_container_width=True):
                        db_global.clear()
                        st.rerun()
                with col_b2:
                    if st.button("🔒 Bloquear", use_container_width=True):
                        st.session_state.modo_organizador = False
                        st.rerun()
