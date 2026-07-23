import streamlit as st
import base64
from groq import Groq

# --- CONFIGURACIÓN DE LA PÁGINA WEB ---
st.set_page_config(
    page_title="Tu asistente de farmacia",
    page_icon="💊",
    layout="centered"
)

# --- CLAVE DE API INTEGRADA (GROQ) ---
CLAVE_API = "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"

# Inicializar cliente de Groq
try:
    client = Groq(api_key=CLAVE_API)
except Exception as e:
    client = None

# --- ESTADOS DE LA SESIÓN (MEMORIA DE LA WEB) ---
if "paciente_actual" not in st.session_state:
    st.session_state.paciente_actual = "Luis (5 años)"

if "historiales_pacientes" not in st.session_state:
    st.session_state.historiales_pacientes = {
      
    }

if "imagen_bytes" not in st.session_state:
    st.session_state.imagen_bytes = None

# --- DISEÑO DE LA INTERFAZ WEB ---
st.title("💊 Tu asistente de farmacia")
st.markdown("---")

# Barra lateral para pacientes y opciones
with st.sidebar:
    st.header("👥 Mis pacientes")
    
    # Selector de paciente actual
    lista_nombres = list(st.session_state.historiales_pacientes.keys())
    indice_actual = lista_nombres.index(st.session_state.paciente_actual) if st.session_state.paciente_actual in lista_nombres else 0
    
    paciente_seleccionado = st.selectbox("Selecciona paciente:", lista_nombres, index=indice_actual)
    if paciente_seleccionado != st.session_state.paciente_actual:
        st.session_state.paciente_actual = paciente_seleccionado
        st.rerun()

    st.markdown("---")
    st.subheader("➕ Agregar paciente")
    nuevo_nombre = st.text_input("Nombre del paciente:")
    nueva_edad = st.text_input("Edad (solo número):")
    
    if st.button("Guardar paciente"):
        if nuevo_nombre.strip() and nueva_edad.strip():
            edad_limpia = ''.join(filter(str.isdigit, nueva_edad.strip()))
            if not edad_limpia:
                edad_limpia = nueva_edad.strip()
            
            clave_p = f"{nuevo_nombre.strip()} ({edad_limpia} años)"
            st.session_state.historiales_pacientes[clave_p] = f"Hola {nuevo_nombre.strip()}, ¿qué medicamento vamos a consultar hoy?"
            st.session_state.paciente_actual = clave_p
            st.success(f"¡Paciente {clave_p} agregado!")
            st.rerun()

    st.markdown("---")
    st.subheader("🖼️ Subir imagen / Foto")
    archivo_subido = st.file_uploader("Sube la foto del medicamento", type=["png", "jpg", "jpeg"])
    if archivo_subido is not None:
        st.session_state.imagen_bytes = archivo_subido.getvalue()
        st.image(st.session_state.imagen_bytes, caption="Imagen cargada", use_column_width=True)
        if st.button("🗑️ Quitar imagen"):
            st.session_state.imagen_bytes = None
            st.rerun()

# --- ÁREA PRINCIPAL DE CHAT Y CONSULTA ---
st.info(f"👦 **Paciente actual:** {st.session_state.paciente_actual}")

# Mostrar respuesta guardada del paciente actual
respuesta_actual = st.session_state.historiales_pacientes.get(st.session_state.paciente_actual, "")

st.markdown("### ✨ Respuesta de la IA")
st.markdown(f"<div style='background-color: #F8FAFC; padding: 15px; border-radius: 10px; border: 1px solid #E2E8F0;'>{respuesta_actual}</div>", unsafe_allow_html=True)

st.markdown("---")

# Cuadro de texto inferior para preguntar
pregunta_usuario = st.text_input("Escribe tu pregunta sobre el medicamento aquí...", placeholder="Ejemplo: ¿Para qué sirve y cuál es la dosis?")

if st.button("Enviar consulta ➔", type="primary"):
    if not client:
        st.error("⚠️ Error: La API Key de Groq no se inicializó correctamente.")
    elif not pregunta_usuario.strip() and not st.session_state.imagen_bytes:
        st.warning("⚠️ Por favor escribe una pregunta o sube una imagen primero.")
    else:
        with st.spinner("⏳ Consultando a Groq IA..."):
            try:
                bytes_img = st.session_state.imagen_bytes
                
                instruccion_idioma = (
                    "IMPORTANTE: Responde SIEMPRE 100% en ESPAÑOL PERUANO natural, claro y como una persona real conversando de frente.\n"
                    f"Actúa como un farmacéutico/enfermero peruano muy humano, cercano y empático que asesora al paciente: {st.session_state.paciente_actual}.\n\n"
                    "REGLAS DE FORMATO Y TÍTULOS:\n"
                    "- Usa etiquetas HTML claras en los títulos principales (ejemplo: <h3><b>1. Nombre del medicamento y presentación</b></h3>) para que se vean perfectamente definidos.\n"
                    "- Usa viñetas limpias para los detalles.\n\n"
                    "REGLAS DE TONO Y CARIÑO SEGÚN EDAD PARA EL 'RESUMEN_VOZ':\n"
                    "- ÚNICAMENTE si el paciente es un NIÑO o BEBÉ (menor de 12 años): Háblale con mucha ternura usando frases como 'mi corazón', 'mi vida' o 'campeón'.\n"
                    "- Si el paciente es un JOVEN o ADULTO (ej. 12 a 59 años): JAMÁS uses expresiones como 'mi corazón' o 'mi vida'. Háblale con mucha amabilidad y respeto profesional.\n"
                    "- Si es un ADULTO MAYOR (60+ años): Háblale con respeto, calidez y mucha paciencia.\n\n"
                    "Sigue ESTRICTAMENTE esta estructura con títulos detallados:\n\n"
                    "<h3><b>1. 💊 Nombre del medicamento y presentación</b></h3>\n"
                    " * Nombre comercial y genérico: [Nombre del medicamento]\n"
                    " * Presentación: [Jarabe, tabletas, gotas, etc.]\n"
                    " * Componentes activos principales: [Principios activos y concentración]\n"
                    " * Promedio de precio en Perú: [Estimado aproximado en Soles peruanos (S/.)]\n\n"
                    "<h3><b>2. 🎯 Usos principales</b></h3>\n"
                    " * Indicación principal: [Para qué sirve específicamente]\n"
                    " * Síntomas que alivia: [Detalle de los síntomas]\n"
                    " * Acción terapéutica: [Cómo ayuda al cuerpo]\n\n"
                    "<h3><b>3. ⏰ Cuándo tomar</b></h3>\n"
                    " * Dosis recomendada: [Dosis sugerida según la edad del paciente]\n"
                    " * Frecuencia y horarios: [Cada cuántas horas y con o sin alimentos]\n"
                    " * Duración habitual del tratamiento: [Días aproximados]\n\n"
                    "<h3><b>4. ⚠️ Cuándo NO tomar</b></h3>\n"
                    " * Contraindicaciones y alergias: [Cuándo evitarlo totalmente]\n"
                    " * Advertencias y precauciones: [Cuidado con otras condiciones o medicamentos]\n"
                    " * Efectos secundarios comunes: [Reacciones leves posibles]\n"
                )
                
                if pregunta_usuario.strip():
                    instruccion_idioma += f"\nConsulta del usuario: {pregunta_usuario}\n"
                else:
                    instruccion_idioma += "\nDescribe y analiza detenidamente lo que ves en la imagen adjunta.\n"

                if bytes_img:
                    modelo_usar = "qwen/qwen3.6-27b"
                    base64_image = base64.b64encode(bytes_img).decode('utf-8')
                    contenido = [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        {"type": "text", "text": instruccion_idioma}
                    ]
                else:
                    modelo_usar = "llama-3.3-70b-versatile"
                    contenido = instruccion_idioma

                response = client.chat.completions.create(
                    model=modelo_usar,
                    messages=[
                        {"role": "system", "content": "Eres un asistente médico y farmacéutico peruano, empático y humano."},
                        {"role": "user", "content": contenido}
                    ],
                    max_tokens=2048
                )
                
                respuesta_texto = response.choices[0].message.content or ""
                st.session_state.historiales_pacientes[st.session_state.paciente_actual] = respuesta_texto
                st.success("¡Consulta completada con éxito!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error al consultar a Groq: {e}")