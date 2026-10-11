import streamlit as st
from acustica_lutherie import AnalizadorTapTuning

# Configuració de la pàgina per a format mòbil
st.set_page_config(
    page_title="FUSTAP - TAP TUNING",
    page_icon="🎸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estil CSS personalitzat per replicar el teu disseny fosc absolut i targetes
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
        font-family: Arial, sans-serif;
    }
    .card {
        background-color: #181818;
        border: 1px solid #2A2A2A;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .title-main {
        font-size: 32px;
        font-weight: bold;
        color: #FFFFFF;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 11px;
        font-weight: bold;
        color: #8E8E93;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Inicialitzar l'analitzador
if 'analizador' not in st.session_state:
    st.session_state.analizador = AnalizadorTapTuning()
    st.session_state.freq_captada = 0.0

# --- CAPÇALERA ---
st.markdown('<p class="title-main">FUSTAP</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">ANÀLISI ACÚSTICA DE PLACA LLIURE</p>', unsafe_allow_html=True)

# --- TARJETA 1: SELECCIÓ DE FUSTA ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<b>SELECCIONA LA FUSTA</b>', unsafe_allow_html=True)
fusta_seleccionada = st.selectbox(
    "", 
    list(st.session_state.analizador.maderas_db.keys()),
    label_visibility="collapsed"
)
st.markdown('</div>', unsafe_allow_html=True)

# --- TARJETA 2: GROIX ACTUAL ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<b>GRUIX ACTUAL DE LA PLACA (MM)</b>', unsafe_allow_html=True)
gruix_str = st.text_input("", placeholder="Ex: 2.8", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# --- TARJETA 3: FREQÜÈNCIA I MICRÒFON ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<b>FREQÜÈNCIA CAPTADA PEL MICRÒFON</b>', unsafe_allow_html=True)
st.markdown(f"<h2 style='text-align: center; color: #FFFFFF;'>{st.session_state.freq_captada} Hz</h2>", unsafe_allow_html=True)

# Botó d'escoltar (al mòbil pot utilitzar l'entrada de veu del navegador)
if st.button("🎙️ ESCOLTAR COP (MICRÒFON)", use_container_width=True):
    try:
        audio = st.session_state.analizador.grabar_golpe()
        st.session_state.freq_captada = st.session_state.analizador.obtener_frecuencia_dominante(audio)
        st.rerun()
    except Exception as e:
        st.error(f"Error de micròfon: {e}")
st.markdown('</div>', unsafe_allow_html=True)

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
    
    # --- TARJETA 4: RESULTATS ---
    st.markdown('<div class="card" style="background-color: #121212;">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)

# --- PEU DE PÀGINA ---
st.markdown("<p style='text-align: center; color: #636366; font-size: 10px; font-weight: bold;'>By: Joan Serrato</p>", unsafe_allow_html=True)
