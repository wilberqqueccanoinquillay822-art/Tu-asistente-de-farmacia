import streamlit as st
from groq import Groq
from gtts import gTTS
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Tu Asistente de Farmacia",
    page_icon="💊",
    layout="centered"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        color: #2c3e50;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .subtitle {
        color: #7f8c8d;
        font-size: 1rem;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #2980b9;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE LA API DE GROQ ---
# Nota: Asegúrate de configurar tu API Key en los Secrets de Streamlit Cloud o reemplazarla aquí temporalmente
api_key = st.secrets.get("GROQ_API_KEY", "TU_API_KEY_AQUI")
client = Groq(api_key=api_key)

# --- GESTIÓN DE PACIENTES EN LA BARRA LATERAL ---
st.sidebar.markdown("### 👥 Mis Pacientes")

# Inicializar lista de pacientes si no existe
if "patients" not in st.session_state:
    st.session_state.patients = [{"name": "Luis", "age": 5}]

# Formulario para agregar paciente en la barra lateral
with st.sidebar.form("add_patient_form", clear_on_submit=True):
    new_name = st.text_input("Nombre del paciente:")
    new_age = st.number_input("Edad (solo número):", min_value=0, max_value=120, value=0)
    submitted = st.form_submit_button("Guardar paciente")
    
    if submitted and new_name:
        st.session_state.patients.append({"name": new_name, "age": int(new_age)})
        st.sidebar.success(f"¡Paciente {new_name} agregado!")

# Selector de paciente actual
patient_names = [f"{p['name']} ({p['age']} años)" for p in st.session_state.patients]
selected_patient_str = st.sidebar.selectbox("Selecciona paciente:", patient_names)

# Extraer el paciente activo
selected_index = patient_names.index(selected_patient_str)
current_patient = st.session_state.patients[selected_index]

# --- CUERPO PRINCIPAL DE LA APLICACIÓN ---
st.markdown('<p class="main-title">💊 Tu asistente de farmacia</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Asesoría farmacéutica inteligente y segura</p>', unsafe_allow_html=True)
st.divider()

# Mostrar paciente actual seleccionado
st.info(f"👤 **Paciente actual:** {current_patient['name']} ({current_patient['age']} años)")

# Entrada de la consulta del usuario
st.markdown("### 🤖 Respuesta de la IA")
user_query = st.text_area(
    "Escribe tu pregunta sobre el medicamento aquí:", 
    placeholder="Ejemplo: ¿Para qué sirve y cuál es la dosis correcta?"
)

# Botón para enviar consulta
if st.button("Enviar consulta ➔"):
    if not user_query.strip():
        st.warning("Por favor, escribe una pregunta antes de enviar.")
    else:
        with st.spinner("Analizando consulta farmacéutica..."):
            try:
                # Prompt del sistema adaptado al paciente
                system_prompt = (
                    f"Eres un asistente de farmacia experto y profesional. "
                    f"Estás atendiendo al paciente {current_patient['name']}, quien tiene {current_patient['age']} años. "
                    f"Proporciona información clara sobre medicamentos, indicaciones y dosis seguras basadas estrictamente en su edad. "
                    f"Si es un niño, advierte consultar siempre a un pediatra."
                )

                # Llamada a la API de Groq
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query}
                    ],
                    model="llama-3.3-70b-versatile", # Puedes cambiar al modelo de tu preferencia
                )

                respuesta_ia = chat_completion.choices[0].message.content

                # Mostrar texto de la respuesta
                st.markdown("---")
                st.write(respuesta_ia)

                # --- MÓDULO DE VOZ (gTTS) ---
                try:
                    tts = gTTS(text=respuesta_ia, lang='es')
                    audio_path = "respuesta_audio.mp3"
                    tts.save(audio_path)
                    
                    # Reproducir audio automáticamente en la web
                    st.audio(audio_path, format="audio/mp3", autoplay=True)
                except Exception as audio_error:
                    st.error(f"No se pudo generar el audio: {audio_error}")

            except Exception as e:
                st.error(f"Ocurrió un error al conectar con la Inteligencia Artificial: {e}")