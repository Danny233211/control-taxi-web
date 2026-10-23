import streamlit as st
import json
import urllib.request
import urllib.error

st.set_page_config(page_title="Control Taxi", page_icon="🚖", layout="wide")

FIREBASE_API_KEY = "AIzaSyAOcup1zGoY9f_2CP4lBYdwBz_vWgacf5U"
FIREBASE_DB_URL = "https://control-taxi-dany-default-rtdb.firebaseio.com/"

def main():
    st.title("🚖 Control de Taxi - Web")
    st.success("¡La aplicación está cargando correctamente!")

if __name__ == "__main__":
    main()
