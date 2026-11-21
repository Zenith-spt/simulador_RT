from datetime import datetime
import io
import pandas as pd
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Simposio 100m - Tiempo de Reacción", page_icon="⏱️", layout="centered")

# Almacenamiento global sincronizado entre todos los dispositivos conectados
@st.cache_resource
def obtener_base_datos():
    return []

db_global = obtener_base_datos()

# Estado local de cada alumno
if "marca_capturada" not in st.session_state:
    st.session_state.marca_capturada = None
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

    # Código JS que mide con precisión de hardware y devuelve el resultado directo a Python
    js_code = f"""
    new Promise((resolve) => {{
        const containerId = 'simposio-tr-box';
        let existing = document.getElementById(containerId);
        if (existing) existing.remove();

        const box = document.createElement('div');
        box.id = containerId;
        box.style.cssText = `
            width: 100%; height: 250px; border-radius: 16px;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            text-align: center; color: white; font-family: sans-serif; font-weight: bold;
            cursor: pointer; user-select: none; -webkit-user-select: none;
            touch-action: manipulation; background-color: #2b5c8f;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-top: 8px;
        `;

        const titulo = document.createElement('div');
        titulo.style.fontSize = '24px';
        titulo.style.padding = '0 15px';
        titulo.innerText = 'TOCA PARA PREPARARTE';

        const sub = document.createElement('div');
        sub.style.fontSize = '15px';
        sub.style.marginTop = '10px';
        sub.style.opacity = '0.9';
        sub.style.padding = '0 20px';
        sub.innerText = 'Reacciona en cuanto percibas la señal.';

        box.appendChild(titulo);
        box.appendChild(sub);
        document.body.appendChild(box);

        let estado = 'inicio';
        let tInicio = 0;
        let timer = null;
        let audioCtx = null;
        const esAuditivo = {str(es_auditivo).lower()};

        function initAudio() {{
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
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

        box.onpointerdown = () => {{
            if (estado === 'inicio' || estado === 'fin') {{
                initAudio();
                estado = 'esperando';
                box.style.backgroundColor = '#d97706';
                titulo.innerText = '🟡 LISTOS...';
                sub.innerText = esAuditivo ? 'Atento al sonido...' : 'Atento al color VERDE...';

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
                sub.innerText = 'Te has adelantado. Toca para repetir.';
                resolve({{ status: 'nula', ts: Date.now() }});

            }} else if (estado === 'estimulo') {{
                const tr = Number((performance.now() - tInicio).toFixed(1));
                estado = 'fin';
                box.style.backgroundColor = '#0284c7';
                box.style.border = 'none';
                titulo.innerText = tr + ' ms';
                sub.innerText = 'Marca capturada. Pulsa el botón de abajo para enviarla o toca aquí para repetir.';
                resolve({{
                    status: 'ok',
                    ms: tr,
                    tipo: esAuditivo ? 'Auditivo' : 'Visual',
                    ts: Date.now()
                }});
            }}
        }};
    }})
    """

    # Ejecuta el cronómetro y recibe el resultado automáticamente en Python
    resultado_js = streamlit_js_eval(js_expressions=js_code, key=f"test_{es_auditivo}", want_output=True)

    # Si hay una marca nueva válida, la guardamos lista para enviar
    if isinstance(resultado_js, dict) and resultado_js.get("status") == "ok":
        st.session_state.marca_capturada = resultado_js

    # Botón único de envío (sin edición manual del tiempo)
    if st.session_state.marca_capturada:
        m = st.session_state.marca_capturada
        ya_enviada = (st.session_state.ultimo_id_enviado == m["ts"])

        st.divider()
        col_info, col_btn = st.columns([1.3, 1])
        with col_info:
            st.markdown(f"**Última marca detectada:** `{m['ms']} ms` ({m['tipo']})")
            if m["ms"] < 100:
                st.caption("⚠️ *Nota: < 100 ms se considera salida nula en World Athletics.*")
        with col_btn:
            if not ya_enviada:
                if st.button(f"📤 Enviar {m['ms']} ms", type="primary", use_container_width=True):
                    nombre_final = participante.strip() if participante.strip() else "Anónimo"
                    db_global.append({
                        "Hora": datetime.now().strftime("%H:%M:%S"),
                        "Participante": nombre_final,
                        "Prueba": m["tipo"],
                        "Tiempo (ms)": m["ms"]
                    })
                    st.session_state.ultimo_id_enviado = m["ts"]
                    st.success("✅ ¡Marca registrada en el ranking!")
                    st.rerun()
            else:
                st.button("✔️ Marca enviada", disabled=True, use_container_width=True)

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

        # Métricas generales
        df_aud = df[df["Prueba"] == "Auditivo"].sort_values(by="Tiempo (ms)").reset_index(drop=True)
        df_vis = df[df["Prueba"] == "Visual"].sort_values(by="Tiempo (ms)").reset_index(drop=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Participaciones", len(df))
        m2.metric("Media Auditiva", f"{df_aud['Tiempo (ms)'].mean():.1f} ms" if not df_aud.empty else "-")
        m3.metric("Media Visual", f"{df_vis['Tiempo (ms)'].mean():.1f} ms" if not df_vis.empty else "-")

        st.divider()

        # Rankings separados lado a lado
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown("### 🔊 Ranking Auditivo")
            if df_aud.empty:
                st.caption("Sin registros auditivos aún.")
            else:
                df_aud.index = df_aud.index + 1  # Posición 1, 2, 3...
                st.dataframe(df_aud[["Participante", "Tiempo (ms)"]], use_container_width=True)

        with col_r2:
            st.markdown("### 🟢 Ranking Visual")
            if df_vis.empty:
                st.caption("Sin registros visuales aún.")
            else:
                df_vis.index = df_vis.index + 1  # Posición 1, 2, 3...
                st.dataframe(df_vis[["Participante", "Tiempo (ms)"]], use_container_width=True)

        st.divider()

        # Descarga directa en Excel (.xlsx) con pestañas separadas y resumen
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
                use_container_width=True
            )
        with col_dl2:
            if st.button("🗑️ Limpiar todos los datos", use_container_width=True):
                db_global.clear()
                st.rerun()
