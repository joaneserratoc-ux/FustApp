import streamlit as st
import numpy as np
import av
import io
from acustica_lutheria import AnalizadorTapTuning
from streamlit_mic_recorder import mic_recorder

# Configuració de la pàgina per a format mòbil
st.set_page_config(
    page_title="FustApp - TAP TUNING",
    page_icon="🎸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estil forçat amb !important perquè Streamlit no sobrescrigui la mida
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
        font-family: Arial, sans-serif;
    }
    .title-main {
        font-size: 80px !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
        letter-spacing: -1px;
        margin-bottom: 0px;
        line-height: 1.1;
    }
    .sub-title {
        font-size: 11px;
        font-weight: bold;
        color: #8E8E93;
        margin-bottom: 25px;
        letter-spacing: 0.5px;
    }
    </style>
""", unsafe_allow_html=True)

# Inicialitzar l'analitzador
if 'analizador' not in st.session_state:
    st.session_state.analizador = AnalizadorTapTuning()
    st.session_state.freq_captada = 0.0

# --- CAPÇALERA ---
st.markdown('<p class="title-main">FustApp</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">ANÀLISI ACÚSTICA DE PLACA LLIURE</p>', unsafe_allow_html=True)

# --- SECCIÓ 1: SELECCIÓ DE FUSTA ---
st.markdown('<b>SELECCIONA LA FUSTA</b>', unsafe_allow_html=True)
fusta_seleccionada = st.selectbox(
    "Fusta", 
    list(st.session_state.analizador.maderas_db.keys()),
    label_visibility="collapsed"
)

st.write("")

# --- SECCIÓ 2: GROIX ACTUAL ---
st.markdown('<b>GRUIX ACTUAL DE LA PLACA (MM)</b>', unsafe_allow_html=True)
gruix_str = st.text_input("Gruix", placeholder="Ex: 2.8", label_visibility="collapsed")

st.write("")

# --- SECCIÓ 3: CAPTURA DE L'ÀUDIO EN DIRECTE ---
st.markdown('<b>CAPTURA DEL COP EN DIRECTE</b>', unsafe_allow_html=True)
st.write("Fes clic un cop i colpeja ràpidament la fusta:")

audio_info = mic_recorder(
    start_prompt="🎙️ CLICA I COLPEJA",
    just_once=True,
    key='mic_automatic'
)

if audio_info and 'bytes' in audio_info:
    try:
        container = av.open(io.BytesIO(audio_info['bytes']))
        audio_stream = container.streams.audio[0]
        
        frames_list = []
        for frame in container.decode(audio_stream):
            sound_array = frame.to_ndarray()
            if len(sound_array.shape) > 1:
                sound_array = sound_array.mean(axis=0)
            frames_list.append(sound_array)
            
        if frames_list:
            audio_data = np.concatenate(frames_list)
            st.session_state.analizador.sample_rate = audio_stream.rate
            st.session_state.freq_captada = st.session_state.analizador.obtener_frecuencia_dominante(audio_data)
    except Exception as e:
        st.error(f"Error processant l'àudio: {e}")

st.markdown(f"<h2 style='text-align: center; color: #FFFFFF; margin-top: 15px;'>{st.session_state.freq_captada} Hz</h2>", unsafe_allow_html=True)

st.write("")

# --- BOTÓ DE CÀLCUL PRINCIPAL ---
if st.button("CALCULAR AJUST DE GRUIX", type="primary", use_container_width=True):
    try:
        grosor_actual = float(gruix_str)
    except ValueError:
        st.warning("Si us plau, introdueix un valor numèric vàlid per al gruix.")
        st.stop()
        
    if st.session_state.freq_captada <= 0:
        st.warning("Primer has de capturar un cop amb el micròfon.")
        st.stop()

    grosor_nou, v_sonido, f_obj = st.session_state.analizador.calcular_ajuste_grosor(
        fusta_seleccionada, grosor_actual, st.session_state.freq_captada
    )
    diferencia = grosor_nou - grosor_actual
    
    # --- RESULTATS ---
    st.markdown("---")
    st.markdown(f"<b>RESULTATS PER A {fusta_seleccionada.upper()}:</b>", unsafe_allow_html=True)
    st.write(f"• Velocitat del so (v): {v_sonido} m/s")
    st.write(f"• Freqüència objectiu: {f_obj} Hz")
    st.write(f"• Gruix òptim calculat: {grosor_nou} mm")
    
    if abs(st.session_state.freq_captada - f_obj) <= 1.5:
        st.success("✅ Freqüència òptima assolida. Placa llesta!")
    elif st.session_state.freq_captada > f_obj:
        st.warning(f"⚠️ Placa rígida. Cal rebaixar ~{abs(diferencia):.2f} mm.")
    else:
        st.info("ℹ️ Placa flexible per sota de l'objectiu. Vigila.")

# --- PEU DE PÀGINA ---
st.markdown("<p style='text-align: center; color: #636366; font-size: 10px; font-weight: bold; margin-top: 35px;'>By: Joan Serrato</p>", unsafe_allow_html=True)
