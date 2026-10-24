import streamlit as st
import json
import urllib.request
import urllib.error

# CONFIGURACIÓN DE LA PÁGINA WEB
st.set_page_config(
    page_title="Control Taxi - Panel Web",
    page_icon="🚖",
    layout="wide"
)

# ESTILOS PARA LIMPIAR LA INTERFAZ DE BOTONES DE DESARROLLO
hide_streamlit_style = """
    <style>
    /* Oculta los botones superiores de Streamlit (Deploy, GitHub, Tres puntos) */
    [data-testid="stAppDeployButton"] { display: none !important; }
    [data-testid="stMainMenu"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    
    /* Oculta el badge flotante inferior */
    .viewerBadge_container__1QSob { display: none !important; }
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
                    return data
    except Exception:
        pass
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
        
        if turno_activo:
            st.warning("⚠️ ¡Hay un turno activo en este momento en la calle!")
            col1, col2, col3 = st.columns(3)
            col1.metric("Chofer", turno_activo.get("chofer", "N/A"))
            col2.metric("Hora de Inicio", turno_activo.get("hora_inicio", "N/A"))
            col3.metric("Km Inicial", f"{turno_activo.get('km_inicio', 0):,.1f} km")
        else:
            st.info("ℹ️ No hay ningún turno abierto en este momento.")

        st.markdown("### 📈 Estadísticas Rápidas del Historial")
        total_turnos = len(turnos)
        ingresos_totales = sum(t.get("total_ingresos", 0) for t in turnos)
        ganancia_dueno_total = sum(t.get("ganancia_neta", 0) for t in turnos)
        km_totales = sum(t.get("km_recorridos", 0) for t in turnos)

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
                            if t.get("deuda_chofer", 0) > 0:
                                st.markdown(f"**A favor del Chófer (Se le debe):** ₡ {t.get('deuda_chofer', 0):,.2f}")
                        else:
                            st.markdown("**Modalidad:** Comisión 30%")
                            
                        st.markdown(f"**Horario:** {t.get('hora_inicio', '')} - {t.get('hora_fin', '')}")
                        st.markdown(f"**Km Recorridos:** {t.get('km_recorridos', 0):,.1f} km")
                        st.markdown("---")
                        
                        st.markdown(f"• **Ingreso Bruto Total Real:** ₡ {t.get('total_ingresos', 0):,.2f}")
                        if es_cuota:
                            st.markdown(f"• **Cuota Fija del Chófer:** ₡ {monto_c:,.2f}")
                        else:
                            st.markdown(f"• **Comisión Chófer (30%):** ₡ {t.get('comision_chofer', 0):,.2f}")
                            st.markdown(f"• **Ingreso menos 30% Chófer:** ₡ {t.get('ingreso_menos_chofer', 0):,.2f}")
                            st.markdown(f"• **Menos Gastos Registrados:** ₡ {t.get('total_gastos', 0):,.2f}")
                        st.markdown(f"• **Ganancia Neta Final (Dueño):** ₡ {t.get('ganancia_neta', 0):,.2f}")
                        
                        st.markdown("---")
                        st.markdown("### 💳 PAGOS RECIBIDOS")
                        st.markdown(f"- **Efectivo:** ₡ {t.get('efectivo', 0):,.2f}")
                        st.markdown(f"- **Datáfono:** ₡ {t.get('datafono', 0):,.2f}")
                        st.markdown(f"- **Sinpe Móvil:** ₡ {t.get('sinpe', 0):,.2f}")
                        
                        if t.get("boletas_coop_bruto", 0) > 0:
                            st.markdown(f"- **Boletas Coop (-12%):** ₡ {t.get('boletas_coop_neto', 0):,.2f} *(Bruto: ₡ {t.get('boletas_coop_bruto', 0):,.2f})*")
                        if t.get("boletas_taxi18_bruto", 0) > 0:
                            st.markdown(f"- **Boletas Taxizarias (-18%):** ₡ {t.get('boletas_taxi18_neto', 0):,.2f} *(Bruto: ₡ {t.get('boletas_taxi18_bruto', 0):,.2f})*")
                        if t.get("boletas_taxi10_bruto", 0) > 0:
                            st.markdown(f"- **Boletas Taxizarias (-10%):** ₡ {t.get('boletas_taxi10_neto', 0):,.2f} *(Bruto: ₡ {t.get('boletas_taxi10_bruto', 0):,.2f})*")
                        
                        st.markdown("---")
                        st.markdown("### ⛽ GASTOS DEL TURNO")
                        st.markdown(f"- **Combustible:** ₡ {t.get('combustible', 0):,.2f}")
                        st.markdown(f"- **Lavado:** ₡ {t.get('lavado', 0):,.2f}")
                        st.markdown(f"- **Peajes:** ₡ {t.get('peajes', 0):,.2f}")
                        st.markdown(f"- **Viáticos:** ₡ {t.get('viaticos', 0):,.2f}")
                        g_extras = t.get("gastos_extras", 0)
                        m_extras = t.get("motivo_extras", "Sin detallar")
                        st.markdown(f"- **Gastos Extras ({m_extras}):** ₡ {g_extras:,.2f}")

    elif menu_opcion == "Historial de Repuestos / Mantenimiento":
        st.title("🛠️ Mantenimientos y Repuestos en la Nube")
        st.markdown("---")
        
        if not mantenimientos:
            st.info("No hay repuestos registrados en la nube.")
        else:
            for idx, m in enumerate(mantenimientos, 1):
                st.markdown(f"""
                **{idx}. {m.get('item', 'Repuesto').capitalize()}**  
                * Fecha: {m.get('fecha')}  
                * Km Realizado: {m.get('km_realizado', 0):,.1f} km  
                * **Costo:** ₡ {m.get('costo', 0):,.2f}  
                """)
                st.markdown("---")

if __name__ == "__main__":
    main()
