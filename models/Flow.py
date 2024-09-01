import gpt_manager


class Flow:
    def __init__(self, id=None, name=None, agent_list=None):
        self.id = id
        self.name = name
        self.agent_list = agent_list

    def process_flow(prompt):
        #for agent in Flow.agent_list:

            
    def chat(flow_id, prompt):
        # Obtener la configuración del GPT desde la base de datos
        gpt_config = gpt_manager.execute_query("SELECT * FROM gpts WHERE id = %s", (gpt_id,), fetchone=True)
        settings = gpt_manager.execute_query("SELECT * FROM settings", fetchone=True)

        if not settings:
            return jsonify({'error': 'settings not found'}), 404

        if not gpt_config:
            return jsonify({'error': 'GPT not found'}), 404

        # Obtener el historial de la conversación desde la base de datos
        conversation_record = gpt_manager.execute_query(
            "SELECT conversation_json FROM conversation_history WHERE flow_id = %s ORDER BY created_at DESC LIMIT 1",
            (flow_id,),
            fetchone=True
        )

        # Preparar el historial de la conversación
        if conversation_record and conversation_record['conversation_json']:
            try:
                conversation_history = json.loads(conversation_record['conversation_json'])
            except json.JSONDecodeError:
                conversation_history = []
        else:
            conversation_history = []

        # Agregar el nuevo mensaje del usuario al historial
        conversation_history.append({"role": "user", "content": prompt})

        # Suponiendo que ya has configurado la clave API en `settings['api_key']`
        openai.api_key = settings['api_key']

        response = openai.ChatCompletion.create(
            model=settings['model'],
            messages=[
                {"role": "system", "content": gpt_config['system_message']},
                *conversation_history  # Incluir el historial completo
            ],
            max_tokens=150,
            temperature=0.7,  # Controla la creatividad de la respuesta
            top_p=1.0,        # Ajuste para el muestreo nucleus
            frequency_penalty=0.0,  # Evita repetir las mismas frases
            presence_penalty=0.0    # Incentiva la introducción de nuevos temas
        )

        # Extraer la respuesta del asistente
        assistant_response = response['choices'][0]['message']['content'].strip()

        # Agregar la respuesta del asistente al historial
        conversation_history.append({"role": "assistant", "content": assistant_response})

        # Guardar el historial actualizado en la base de datos
        gpt_manager.execute_query(
            "INSERT INTO conversation_history (gpt_id, conversation_json) VALUES (%s, %s)",
            (gpt_id, json.dumps(conversation_history))
        )

        # Devolver la respuesta del asistente al usuario
        return jsonify({'response': assistant_response})



