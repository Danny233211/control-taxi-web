import streamlit as st
import json
import urllib.request
import urllib.error

st.set_page_config(page_title="Control Taxi", page_icon="🚖", layout="wide")

FIREBASE_API_KEY = "AIzaSyAOcup1zGoY9f_2CP4lBYdwBz_vWgacf5U"
FIREBASE_DB_URL = "https://control-taxi-dany-default-rtdb.firebaseio.com/"

def iniciar_sesion_firebase(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = json.dumps({"email": email, "password": password, "returnSecureToken": True}).encode("utf-8")
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

    if not st.session_state.uid:
        st.markdown("<h2 style='text-align: center; color: #FFD700;'>🚖 CONTROL DE TAXI - PANEL WEB</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #AAAAAA;'>Ingrese con su cuenta de Firebase</p>", unsafe_allow_html=True)
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
                        st.warning("Complete ambos campos.")
        return

    st.sidebar.title("🚖 Menú Web")
    st.sidebar.markdown(f"**Usuario:** `{st.session_state.email}`")
    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state.uid = None
        st.session_state.email = None
        st.rerun()

    datos = cargar_datos_nube(st.session_state.uid)
    st.title("📊 Panel de Control de Taxi")
    st.success("¡Conectado exitosamente a la base de datos en la nube!")
    st.write(f"Total de turnos guardados: {len(datos.get('turnos', []))}")

if __name__ == "__main__":
    main()
