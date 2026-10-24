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

# ESTILOS LIMPIOS PARA OCULTAR MENÚ Y BRANDING SIN AFECTAR LOS FORMULARIOS
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stToolbar"] {visibility: hidden; display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

FIREBASE_API_KEY = "AIzaSyAOcup1zGoY9f_2CP4lBYdwBz_vWgacf5U"
FIREBASE_DB_URL = "https://control-taxi-dany-default-rtdb.firebaseio.com/"

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

    # Panel Principal con Menú
    st.sidebar.title("🚖 Menú Web")
    st.sidebar.markdown(f"**Usuario:** `{st.session_state.email}`")
    
    menu_opcion = st.sidebar.radio(
        "Seleccione una opción:",
        ["Resumen en Vivo", "Consultar Reportes por Fecha", "Historial de Repuestos / Mantenimiento"]
    )
    
    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state.uid = None
        st.session_state.email = None
        st.rerun()

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
            fecha_busqueda = st.text_input("Ingrese la fecha a consultar (Formato: DD-MM-YYYY o MM-YYYY)", placeholder="ej: 23-10-2026")
            if st.button("Buscar Reporte"):
                if fecha_busqueda:
                    filtrados = [t for t in turnos if t.get("fecha") == fecha_busqueda or t.get("fecha", "").endswith(fecha_busqueda)]
                    if not filtrados:
                        st.error(f"No se encontraron registros para: {fecha_busqueda}")
                    else:
                        st.success(f"Se encontraron {len(filtrados)} turno(s):")
                        for idx, t in enumerate(filtrados, 1):
                            with st.expander(f"Turno #{idx} - Chofer: {t.get('chofer')} ({t.get('fecha')})"):
                                st.write(f"**Horario:** {t.get('hora_inicio')} - {t.get('hora_fin')}")
                                st.write(f"**Km Recorridos:** {t.get('km_recorridos', 0):,.1f} km")
                                st.write(f"**Ingreso Bruto Total:** ₡ {t.get('total_ingresos', 0):,.2f}")
                                st.write(f"**Ganancia Neta Final (Dueño):** ₡ {t.get('ganancia_neta', 0):,.2f}")
                else:
                    st.warning("Por favor ingrese una fecha.")

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
