import streamlit as st
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# CONFIGURACIÓN DE LA PÁGINA WEB
st.set_page_config(
    page_title="Control Taxi - Panel Web",
    page_icon="🚖",
    layout="wide"
)

# ESTILOS PARA LIMPIAR LA INTERFAZ Y PREPARAR IMPRESIÓN
hide_streamlit_style = """
    <style>
    /* Oculta los botones superiores de Streamlit */
    [data-testid="stAppDeployButton"] { display: none !important; }
    [data-testid="stMainMenu"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    
    /* Oculta el badge flotante inferior */
    .viewerBadge_container__1QSob { display: none !important; }
    
    /* Estilos para impresión limpia */
    @media print {
        header, footer, nav, .stButton, button, [data-testid="stForm"], select, input {
            display: none !important;
        }
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

FIREBASE_API_KEY = "AIzaSyAOcup1zGoY9f_2CP4lBYdwBz_vWgacf5U"
FIREBASE_DB_URL = "https://control-taxi-app-default-rtdb.firebaseio.com"

def iniciar_sesion_firebase(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data.get("localId"), None
    except Exception:
        return None, "Correo o contraseña incorrectos."
    return None, "Error desconocido."

def cargar_datos_nube(uid):
    url = f"{FIREBASE_DB_URL}/usuarios/{uid}/datos_taxi.json"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data:
                    if "turno_activo" not in data: data["turno_activo"] = None
                    if "turnos" not in data: data["turnos"] = []
                    if "mantenimientos" not in data: data["mantenimientos"] = []
                    return data
    except Exception as e:
        print(f"Error cargando de nube: {e}")
    
    return {"turnos": [], "mantenimientos": [], "turno_activo": None}

def main():
    if "uid" not in st.session_state:
        st.session_state.uid = None
    if "email" not in st.session_state:
        st.session_state.email = None

    # Pantalla de Login
    if not st.session_state.uid:
        st.markdown("<h2 style='text-align: center; color: #FFD700;'>🚖 CONTROL DE TAXI - PANEL WEB</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #AAAAAA;'>Ingrese con su cuenta de Firebase para ver sus datos</p>", unsafe_allow_html=True)
        
        _, col2, _ = st.columns([1, 2, 1])
        with col2:
            with st.form("form_login"):
                email_input = st.text_input("Correo electrónico")
                password_input = st.text_input("Contraseña", type="password")
                btn_enviar = st.form_submit_button("Iniciar Sesión", use_container_width=True)
                
                if btn_enviar:
                    if email_input and password_input:
                        uid, error = iniciar_sesion_firebase(email_input.strip(), password_input.strip())
                        if uid:
                            st.session_state.uid = uid
                            st.session_state.email = email_input
                            st.rerun()
                        else:
                            st.error(error)
                    else:
                        st.warning("Por favor complete ambos campos.")
        return

    # Panel Principal
    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.markdown(f"👤 **Usuario Conectado:** `{st.session_state.email}`")
    with col_btn:
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.uid = None
            st.session_state.email = None
            st.rerun()

    # Barra lateral de diagnóstico para verificar que el UID y Firebase coinciden perfectamente
    with st.sidebar:
        st.markdown("### 🔍 Diagnóstico de Conexión")
        st.text(f"UID: {st.session_state.uid}")
        if st.button("Probar Conexión Firebase"):
            url_test = f"{FIREBASE_DB_URL}/usuarios/{st.session_state.uid}/datos_taxi.json"
            try:
                req = urllib.request.Request(url_test)
                with urllib.request.urlopen(req) as resp:
                    if resp.status == 200:
                        raw_data = resp.read().decode('utf-8')
                        st.success("¡Conexión exitosa con Firebase!")
                        st.json(json.loads(raw_data) if raw_data != "null" else {"estado": "Nodo vacío"})
            except Exception as ex:
                st.error(f"Error al conectar: {ex}")

    st.markdown("---")

    menu_opcion = st.selectbox(
        "📌 Seleccione la sección que desea consultar:",
        ["Resumen en Vivo", "Consultar Reportes por Fecha", "Historial de Repuestos / Mantenimiento"]
    )
    
    st.markdown("---")

    datos = cargar_datos_nube(st.session_state.uid)
    turnos = datos.get("turnos", [])
    mantenimientos = datos.get("mantenimientos", [])
    turno_activo = datos.get("turno_activo", None)

    if menu_opcion == "Resumen en Vivo":
        st.title("📊 Estado Actual y Resumen en Vivo")
        st.markdown("---")
        
        if turno_activo and isinstance(turno_activo, dict):
            st.warning("⚠️ ¡Hay un turno activo en este momento en la calle!")
            col1, col2, col3 = st.columns(3)
            col1.metric("Chofer", turno_activo.get("chofer", "N/A"))
            col2.metric("Hora de Inicio", turno_activo.get("hora_inicio", "N/A"))
            col3.metric("Km Inicial", f"{turno_activo.get('km_inicio', 0):,.1f} km")
            
            modo_str = "Cuota Fija" if turno_activo.get('es_cuota', False) else "Comisión 30%"
            st.info(f"📋 **Modalidad de trabajo:** {modo_str}")
        else:
            st.info("ℹ️ No hay ningún turno abierto en este momento.")

        st.markdown("### 📈 Estadísticas del Historial")
        
        # Selector de filtro temporal
        filtro_tiempo = st.radio(
            "Filtrar estadísticas por período:",
            ["Todo el Historial", "Esta Semana (Lunes a Domingo)", "Este Mes", "Este Año"],
            horizontal=True
        )
        
        hoy = datetime.now()
        turnos_filtrados_stats = []

        for t in turnos:
            fecha_str = t.get("fecha", "")
            try:
                parts = fecha_str.split("-")
                if len(parts) == 3:
                    fecha_dt = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
                    
                    if filtro_tiempo == "Esta Semana (Lunes a Domingo)":
                        inicio_semana = hoy - timedelta(days=hoy.weekday())
                        inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
                        fin_semana = inicio_semana + timedelta(days=6, hours=23, minutes=59, seconds=59)
                        if inicio_semana <= fecha_dt <= fin_semana:
                            turnos_filtrados_stats.append(t)
                            
                    elif filtro_tiempo == "Este Mes":
                        if fecha_dt.year == hoy.year and fecha_dt.month == hoy.month:
                            turnos_filtrados_stats.append(t)
                            
                    elif filtro_tiempo == "Este Año":
                        if fecha_dt.year == hoy.year:
                            turnos_filtrados_stats.append(t)
                            
                    else:
                        turnos_filtrados_stats.append(t)
                else:
                    if filtro_tiempo == "Todo el Historial":
                        turnos_filtrados_stats.append(t)
            except Exception:
                if filtro_tiempo == "Todo el Historial":
                    turnos_filtrados_stats.append(t)

        total_turnos = len(turnos_filtrados_stats)
        ingresos_totales = sum(t.get("total_ingresos", 0) for t in turnos_filtrados_stats)
        ganancia_dueno_total = sum(t.get("ganancia_neta", 0) for t in turnos_filtrados_stats)
        km_totales = sum(t.get("km_recorridos", 0) for t in turnos_filtrados_stats)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Turnos Registrados", total_turnos)
        c2.metric("Km Recorridos", f"{km_totales:,.1f} km")
        c3.metric("Ingresos Totales", f"₡ {ingresos_totales:,.2f}")
        c4.metric("Ganancia Neta (Dueño)", f"₡ {ganancia_dueno_total:,.2f}")

    elif menu_opcion == "Consultar Reportes por Fecha":
        st.title("📅 Consulta de Reportes Históricos")
        st.markdown("---")
        
        if not turnos:
            st.info("No hay turnos registrados en la nube todavía.")
        else:
            fecha_busqueda = st.text_input("Ingrese la fecha a consultar (Formato: DD-MM-YYYY o MM-YYYY)", placeholder="ej: 24-10-2026")
            
            if fecha_busqueda.strip():
                filtrados = [t for t in turnos if t.get("fecha") == fecha_busqueda.strip() or t.get("fecha", "").endswith(fecha_busqueda.strip())]
            else:
                filtrados = turnos

            if not filtrados:
                st.error(f"No se encontraron registros para: {fecha_busqueda}")
            else:
                st.success(f"Se encontraron {len(filtrados)} turno(s):")
                for idx, t in enumerate(filtrados, 1):
                    es_cuota = t.get("es_cuota", False)
                    monto_c = t.get("monto_cuota", 0)
                    
                    with st.expander(f"Turno #{idx} - Chofer: {t.get('chofer')} ({t.get('fecha')})"):
                        st.markdown(f"**Chofer:** {t.get('chofer', 'No especificado')}")
                        if es_cuota:
                            st.markdown(f"**Modalidad:** Cuota Fija (₡ {monto_c:,.2f})")
                        else:
                            st.markdown("**Modalidad:** Comisión 30%")
                            
                        st.markdown(f"**Horario:** {t.get('hora_inicio', '')} - {t.get('hora_fin', '')}")
                        st.markdown(f"**Km Recorridos:** {t.get('km_recorridos', 0):,.1f} km")
                        st.markdown("---")
                        
                        st.markdown(f"• **1. Ingreso Bruto Total Real:** ₡ {t.get('total_ingresos', 0):,.2f}")
                        if es_cuota:
                            st.markdown(f"• **2. Cuota Fija del Chófer:** ₡ {monto_c:,.2f}")
                        else:
                            st.markdown(f"• **2. Comisión Chófer (30%):** ₡ {t.get('comision_chofer', 0):,.2f}")
                            st.markdown(f"• **3. Ingreso menos 30% Chófer:** ₡ {t.get('ingreso_menos_chofer', 0):,.2f}")
                            st.markdown(f"• **4. Menos Gastos Registrados:** ₡ {t.get('total_gastos', 0):,.2f}")
                        st.markdown(f"• **5. Ganancia Neta Final (Dueño):** ₡ {t.get('ganancia_neta', 0):,.2f}")
                        
                        st.markdown("---")
                        st.markdown("### 💳 PAGOS RECIBIDOS")
                        
                        efectivo = t.get('efectivo', 0)
                        datafono = t.get('datafono', 0)
                        sinpe = t.get('sinpe', 0)
                        b_coop_neto = t.get('boletas_coop_neto', 0)
                        b_taxi18_neto = t.get('boletas_taxi18_neto', 0)
                        b_taxi10_neto = t.get('boletas_taxi10_neto', 0)
                        
                        total_digitales = datafono + sinpe + b_coop_neto + b_taxi18_neto + b_taxi10_neto
                        
                        st.markdown(f"- **Efectivo:** ₡ {efectivo:,.2f}")
                        st.markdown(f"- **Datáfono:** ₡ {datafono:,.2f}")
                        st.markdown(f"- **Sinpe Móvil:** ₡ {sinpe:,.2f}")
                        
                        if t.get("boletas_coop_bruto", 0) > 0:
                            st.markdown(f"- **Boletas Coop (-12%):** ₡ {b_coop_neto:,.2f} *(Bruto: ₡ {t.get('boletas_coop_bruto', 0):,.2f})*")
                        if t.get("boletas_taxi18_bruto", 0) > 0:
                            st.markdown(f"- **Boletas Taxizarias (-18%):** ₡ {b_taxi18_neto:,.2f} *(Bruto: ₡ {t.get('boletas_taxi18_bruto', 0):,.2f})*")
                        if t.get("boletas_taxi10_bruto", 0) > 0:
                            st.markdown(f"- **Boletas Taxizarias (-10%):** ₡ {b_taxi10_neto:,.2f} *(Bruto: ₡ {t.get('boletas_taxi10_bruto', 0):,.2f})*")
                        
                        st.markdown(f"- 📲 **Total Pagos Digitales / No Efectivo:** ₡ {total_digitales:,.2f}")

                        st.markdown("---")
                        if not es_cuota:
                            st.markdown("### 🤝 COMISIÓN CHÓFER (30%)")
                            st.markdown(f"- **Comisión Total (30%):** ₡ {t.get('comision_chofer', 0):,.2f}")
                            st.markdown(f"- **El chófer agarró en efectivo:** ₡ {t.get('efectivo_retirado_chofer', 0):,.2f}")
                            deuda = t.get('deuda_chofer', 0)
                            if deuda > 0:
                                st.markdown(f"- 🔴 **A favor del chófer (Se le debe):** ₡ {deuda:,.2f}")
                            else:
                                st.markdown("- 🟢 **Comisión pagada completa en el turno**")
                            st.markdown("---")

                        st.markdown("### ⛽ GASTOS DEL TURNO")
                        st.markdown(f"- **Combustible:** ₡ {t.get('combustible', 0):,.2f}")
                        st.markdown(f"- **Lavado:** ₡ {t.get('lavado', 0):,.2f}")
                        st.markdown(f"- **Peajes:** ₡ {t.get('peajes', 0):,.2f}")
                        st.markdown(f"- **Viáticos:** ₡ {t.get('viaticos', 0):,.2f}")
                        g_extras = t.get("gastos_extras", 0)
                        m_extras = t.get("motivo_extras", "Sin detallar")
                        st.markdown(f"- **Gastos Extras ({m_extras}):** ₡ {g_extras:,.2f}")
                        
                        st.markdown("---")
                        
                        resumen_txt = f"""==========================================
   REPORTE DE TURNO - CONTROL DE TAXI
==========================================
Fecha: {t.get('fecha')}
Chofer: {t.get('chofer')}
Horario: {t.get('hora_inicio')} - {t.get('hora_fin')}
Km Recorridos: {t.get('km_recorridos', 0):,.1f} km

1. Ingreso Bruto Total: Colones {t.get('total_ingresos', 0):,.2f}
2. Ganancia Neta (Dueño): Colones {t.get('ganancia_neta', 0):,.2f}

PAGOS RECIBIDOS:
- Efectivo: Colones {efectivo:,.2f}
- Datáfono: Colones {datafono:,.2f}
- Sinpe Móvil: Colones {sinpe:,.2f}
- Total Pagos Digitales: Colones {total_digitales:,.2f}

COMISIÓN CHÓFER (30%):
- Comisión Total: Colones {t.get('comision_chofer', 0):,.2f}
- Agarró en efectivo: Colones {t.get('efectivo_retirado_chofer', 0):,.2f}
- A favor del chófer (deuda): Colones {t.get('deuda_chofer', 0):,.2f}

GASTOS DEL TURNO:
- Combustible: Colones {t.get('combustible', 0):,.2f}
- Lavado: Colones {t.get('lavado', 0):,.2f}
- Peajes: Colones {t.get('peajes', 0):,.2f}
- Viáticos: Colones {t.get('viaticos', 0):,.2f}
- Extras ({m_extras}): Colones {g_extras:,.2f}
=========================================="""

                        col_exp1, col_exp2 = st.columns(2)
                        
                        with col_exp1:
                            st.download_button(
                                label="📥 Descargar Reporte (.TXT)",
                                data=resumen_txt,
                                file_name=f"reporte_taxi_{t.get('fecha')}_{t.get('chofer')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                            
                        with col_exp2:
                            btn_html = """
                            <button onclick="window.print()" style="
                                width: 100%;
                                background-color: #008CBA;
                                color: white;
                                padding: 8px 16px;
                                border: none;
                                border-radius: 4px;
                                cursor: pointer;
                                font-weight: bold;
                                font-size: 14px;">
                                🖨️ Imprimir / Guardar en PDF
                            </button>
                            """
                            st.components.v1.html(btn_html, height=45)

    elif menu_opcion == "Historial de Repuestos / Mantenimiento":
        st.title("🛠️ Mantenimientos y Repuestos en la Nube")
        st.markdown("---")
        
        if not mantenimientos:
            st.info("No hay repuestos registrados en la nube.")
        else:
            for idx, m in enumerate(mantenimientos, 1):
                nombre_repuesto = m.get('item', m.get('pieza', 'Repuesto'))
                st.markdown(f"""
                **{idx}. {nombre_repuesto.capitalize()}**  
                * Fecha: {m.get('fecha')}  
                * Km Realizado: {m.get('km_realizado', 0):,.1f} km  
                * **Costo:** ₡ {m.get('costo', 0):,.2f}  
                """)
                st.markdown("---")

if __name__ == "__main__":
    main()
