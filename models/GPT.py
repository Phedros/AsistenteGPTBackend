import json
import openai
import gpt_manager
from conversation import save_conversation, get_conversation_history
from models.flujo import Flujo  # Importa las funciones necesarias

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

    def get_chat_response(self, prompt, conversation_id=None, flujo_id=None):
        """
        Obtiene la respuesta del chat del GPT basado en el prompt y actualiza el historial de la conversación.
        
        :param prompt: Mensaje del usuario.
        :param conversation_id: ID de la conversación (fuera de un flujo).
        :param flujo_id: ID del flujo (si se está en un flujo multiagente).
        :return: Respuesta del asistente.
        """
        # Obtener la configuración del GPT desde la base de datos
        settings = gpt_manager.execute_query("SELECT * FROM settings", fetchone=True)

        if not settings:
            raise ValueError("Settings not found")

        # Historial de conversación será manejado diferentemente si estamos en un flujo
        if flujo_id:
            #conversation = []
            # Obtener el historial del flujo desde la base de datos utilizando el flujo_id
            conversation_history = Flujo.obtener_historial_flujo(conversation_id)
        else:
            # Obtener el historial de la conversación desde la base de datos utilizando el conversation_id
            conversation_history = get_conversation_history(conversation_id)

        # Agregar el nuevo mensaje del usuario al historial
        conversation_history.append({"role": "user", "content": prompt})
        #conversation.append({"role": "user", "content": prompt})

        # Configurar la API de OpenAI
        openai.api_key = settings['api_key']

        response = openai.ChatCompletion.create(
            model=settings['model'],
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt}
            ],
            #max_tokens=500,
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
        if flujo_id:
            # Actualizar el historial del flujo en una sola fila en flujo_conversation_history
            Flujo.actualizar_historial_flujo(flujo_id, conversation_history)
        else:
            # Actualizar el historial de conversación normal
            save_conversation(conversation_id, conversation_history)

        return assistant_response




    @staticmethod
    def get_gpt_by_id(gpt_id):
        data = gpt_manager.execute_query("SELECT * FROM gpts WHERE id = %s", (gpt_id,), fetchone=True)
        if data:
            return GPT(data['id'], data['name'], data['model'], data['system_message'])
        return None

    # Puedes agregar más métodos según lo necesites
