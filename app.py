import json
from flask import Flask, request, jsonify
import openai
import gpt_manager
import conversation

app = Flask(__name__)

@app.route('/gpts', methods=['GET'])
def get_gpts():
    gpts = gpt_manager.execute_query("SELECT id, name, api_key, model, system_message FROM gpts", fetchall=True)
    return jsonify(gpts), 200

@app.route('/gpt/create', methods=['POST'])
def create_gpt():
    data = request.json
    gpt_manager.create_gpt(
        name=data['name'],
        api_key=data['api_key'],
        model=data.get('model', 'gpt-4o-mini'),
        system_message=data.get('system_message', 'You are a helpful assistant.')
    )
    return jsonify({'message': 'GPT created successfully'}), 201

@app.route('/gpt/update/<int:gpt_id>', methods=['POST'])
def update_gpt(gpt_id):
    data = request.json
    try:
        gpt_manager.update_gpt(
            gpt_id,
            name=data.get('name'),
            api_key=data.get('api_key'),
            model=data.get('model'),
            system_message=data.get('system_message')
        )
        return jsonify({'message': 'GPT updated successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/gpt/delete/<int:gpt_id>', methods=['DELETE'])
def delete_gpt(gpt_id):
    gpt_manager.delete_gpt(gpt_id)
    return jsonify({'message': 'GPT deleted successfully'}), 200

@app.route('/gpt/history/<int:gpt_id>', methods=['GET'])
def get_history(gpt_id):
    history = conversation.get_conversation_history(gpt_id)
    return jsonify(history), 200

@app.route('/gpt/chat/<int:gpt_id>', methods=['POST'])
def chat(gpt_id):
    # Obtener el mensaje del usuario desde el cuerpo de la solicitud
    prompt = request.json.get('prompt')

    # Obtener la configuración del GPT desde la base de datos
    gpt_config = gpt_manager.execute_query("SELECT * FROM gpts WHERE id = %s", (gpt_id,), fetchone=True)

    if not gpt_config:
        return jsonify({'error': 'GPT not found'}), 404

    # Obtener el historial de la conversación desde la base de datos
    conversation_record = gpt_manager.execute_query(
        "SELECT conversation_json FROM conversation_history WHERE gpt_id = %s ORDER BY created_at DESC LIMIT 1",
        (gpt_id,),
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

    # Suponiendo que ya has configurado la clave API en `gpt_config['api_key']`
    openai.api_key = gpt_config['api_key']

    response = openai.ChatCompletion.create(
        model=gpt_config['model'],
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


if __name__ == '__main__':
    app.run(debug=True)
