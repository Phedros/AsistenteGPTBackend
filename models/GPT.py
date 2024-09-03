import json
import openai
import gpt_manager
from conversation import save_conversation, get_conversation_history  # Importa las funciones necesarias

class GPT:
    def __init__(self, id=None, name=None, model=None, system_message=None):
        self.id = id
        self.name = name
        self.model = model
        self.system_message = system_message

    def save(self):
        if self.id is None:
            # Insertar nuevo GPT en la base de datos
            self.id = gpt_manager.create_gpt(self.name, self.model, self.system_message)
        else:
            # Actualizar GPT existente
            gpt_manager.update_gpt(self.id, self.name, self.model, self.system_message)

    def delete(self):
        gpt_manager.delete_gpt(self.id)

    @staticmethod
    def get_gpt_by_id(gpt_id):
        data = gpt_manager.execute_query("SELECT * FROM gpts WHERE id = %s", (gpt_id,), fetchone=True)
        if data:
            return GPT(data['id'], data['name'], data['model'], data['system_message'])
        return None

    def get_chat_response(self, prompt, conversation_id):
        # Obtener la configuración del GPT desde la base de datos
        settings = gpt_manager.execute_query("SELECT * FROM settings", fetchone=True)

        if not settings:
            raise ValueError("Settings not found")

        # Obtener el historial de la conversación desde la base de datos utilizando el conversation_id
        conversation_history = get_conversation_history(conversation_id)

        # Agregar el nuevo mensaje del usuario al historial
        conversation_history.append({"role": "user", "content": prompt})

        # Configurar la API de OpenAI
        openai.api_key = settings['api_key']

        response = openai.ChatCompletion.create(
            model=settings['model'],
            messages=[
                {"role": "system", "content": self.system_message},
                *conversation_history  # Incluir el historial completo
            ],
            max_tokens=150,
            temperature=0.7,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        # Extraer la respuesta del asistente
        assistant_response = response['choices'][0]['message']['content'].strip()

        # Agregar la respuesta del asistente al historial
        conversation_history.append({"role": "assistant", "content": assistant_response})

        # Guardar el historial actualizado en la base de datos
        save_conversation(conversation_id, conversation_history)

        return assistant_response



    @staticmethod
    def get_gpt_by_id(gpt_id):
        data = gpt_manager.execute_query("SELECT * FROM gpts WHERE id = %s", (gpt_id,), fetchone=True)
        if data:
            return GPT(data['id'], data['name'], data['model'], data['system_message'])
        return None

    # Puedes agregar más métodos según lo necesites
