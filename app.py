import streamlit as st
from openai import OpenAI
import os

# Configurar la página de Streamlit
st.set_page_config(page_title="Asistente de OpenAI", page_icon="🤖")

st.title("Asistente de OpenAI")

# Obtener la clave API de OpenAI desde las variables de entorno
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    # Configurar el cliente OpenAI con la clave obtenida
    client = OpenAI(api_key=api_key)

    try:
        # Obtener la lista de asistentes disponibles
        my_assistants = client.beta.assistants.list()
        assistant_names = [assistant.name for assistant in my_assistants.data]
        assistant_ids = [assistant.id for assistant in my_assistants.data]

        # Seleccionar un asistente
        assistant_index = st.selectbox(
            "Selecciona un asistente",
            range(len(assistant_names)),
            format_func=lambda x: assistant_names[x]
        )
        assistant_id = assistant_ids[assistant_index]

        # Inicializar variables de sesión
        if 'assistant_id' not in st.session_state:
            st.session_state.assistant_id = assistant_id
            st.session_state.thread_id = None  # Reiniciar el thread_id
            st.session_state.messages = []     # Reiniciar el historial de mensajes
        else:
            # Si se selecciona un asistente diferente, reiniciar el estado
            if st.session_state.assistant_id != assistant_id:
                st.session_state.assistant_id = assistant_id
                st.session_state.thread_id = None
                st.session_state.messages = []

        if 'thread_id' not in st.session_state or st.session_state.thread_id is None:
            # Crear un nuevo hilo de conversación
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id

        if 'messages' not in st.session_state:
            st.session_state.messages = []

        # Mostrar el historial de la conversación
        for msg in st.session_state.messages:
            with st.chat_message(msg['role']):
                st.markdown(msg['content'])

        # Entrada de mensaje del usuario utilizando st.chat_input
        user_message = st.chat_input("Escribe tu mensaje")

        if user_message:
            # Mostrar el mensaje del usuario inmediatamente
            with st.chat_message("user"):
                st.markdown(user_message)

            # Guardar el mensaje del usuario en la sesión
            st.session_state.messages.append({'role': 'user', 'content': user_message})

            with st.spinner('Obteniendo respuesta...'):
                # Crear el mensaje en el hilo
                message = client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=user_message
                )

                # Iniciar la ejecución del asistente
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id,
                    assistant_id=st.session_state.assistant_id
                )

                # Esperar a que se complete la ejecución
                run_status = client.beta.threads.runs.poll(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )

                if run_status.status == 'completed':
                    # Obtener la respuesta del asistente
                    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
                    assistant_messages = [
                        msg for msg in messages.data
                        if msg.role == "assistant" and msg.run_id == run.id
                    ]
                    if assistant_messages:
                        latest_message = assistant_messages[-1]
                        response = ''.join([block.text.value for block in latest_message.content])

                        # Guardar la respuesta del asistente en la sesión
                        st.session_state.messages.append({'role': 'assistant', 'content': response})

                        # Mostrar la respuesta del asistente
                        with st.chat_message("assistant"):
                            st.markdown(response)
                    else:
                        st.error("No se recibió respuesta del asistente.")
                else:
                    st.error(f"Estado de ejecución: {run_status.status}")

    except Exception as e:
        st.error(f"Error al obtener los asistentes o al procesar la conversación: {e}")
else:
    st.error("La clave API de OpenAI no se encontró en las variables de entorno. Por favor, configúrala antes de continuar.")
