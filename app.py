import json
from flask import Flask, request, jsonify
import openai
import gpt_manager
import conversation
from models.GPT import GPT as GPTClass

app = Flask(__name__)

@app.route('/gpts', methods=['GET'])
def get_gpts():
    gpts = gpt_manager.execute_query("SELECT id, name, model, system_message FROM gpts", fetchall=True)
    return jsonify(gpts), 200

@app.route('/gpt/create', methods=['POST'])
def create_gpt():
    settings = gpt_manager.execute_query("SELECT * FROM settings", fetchone=True)
    data = request.json
    gpt = GPTClass(
        name=data.get('name'),
        model=data.get('model') or settings['model'],
        system_message=data.get('system_message')
    )
    if not gpt.name or not gpt.system_message:
        return jsonify({'error': 'El nombre y el mensaje del sistema son obligatorios.'}), 400
    gpt.save()
    return jsonify({'message': 'GPT created successfully'}), 201



@app.route('/gpt/update/<int:gpt_id>', methods=['POST'])
def update_gpt(gpt_id):
    gpt = GPTClass.get_gpt_by_id(gpt_id)
    if not gpt:
        return jsonify({'error': 'GPT not found'}), 404
    data = request.json
    gpt.name = data.get('name', gpt.name)
    gpt.model = data.get('model', gpt.model)
    gpt.system_message = data.get('system_message', gpt.system_message)
    gpt.save()
    return jsonify({'message': 'GPT updated successfully'}), 200

@app.route('/gpt/delete/<int:gpt_id>', methods=['DELETE'])
def delete_gpt(gpt_id):
    gpt_manager.delete_gpt(gpt_id)
    return jsonify({'message': 'GPT deleted successfully'}), 200

@app.route('/gpt/history/<int:gpt_id>', methods=['GET'])
def get_history(gpt_id):
    history = conversation.get_conversation_history(gpt_id)
    if history is None:
        return jsonify({'error': 'No history found for the specified GPT.'}), 404
    return jsonify(history), 200

# Nueva ruta para borrar el historial de un GPT específico
@app.route('/gpt/history/delete/<int:gpt_id>', methods=['DELETE'])
def delete_history(gpt_id):
    try:
        conversation.delete_conversation_history(gpt_id)
        return jsonify({'message': 'History deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/gpt/chat/<int:gpt_id>', methods=['POST'])
def chat(gpt_id):
    prompt = request.json.get('prompt')

    # Obtener el objeto GPT desde la base de datos
    gpt = GPTClass.get_gpt_by_id(gpt_id)
    if not gpt:
        return jsonify({'error': 'GPT not found'}), 404

    try:
        # Usar el método de la clase GPT para obtener la respuesta del chat
        response = gpt.get_chat_response(prompt)
        return jsonify({'response': response}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Endpoint para actualizar la configuración
@app.route('/settings/update', methods=['POST'])
def update_settings():
    data = request.json
    if 'api_key' in data and 'model' in data:
        # Verifica si hay filas en la tabla
        check_query = "SELECT COUNT(*) as count FROM settings"
        result = gpt_manager.execute_query(check_query, fetchone=True)
        
        if result['count'] == 0:
            # Inserta una nueva fila si la tabla está vacía
            insert_query = "INSERT INTO settings (api_key, model) VALUES (%s, %s)"
            gpt_manager.execute_query(insert_query, params=(data['api_key'], data['model']))
        else:
            # Si hay al menos una fila, realiza el UPDATE
            update_query = """
            UPDATE settings 
            SET api_key = %s, model = %s
            """
            gpt_manager.execute_query(update_query, params=(data['api_key'], data['model']))
        
        return jsonify({'message': 'Configuración actualizada exitosamente.'}), 200
    else:
        return jsonify({'error': 'Faltan datos en la solicitud.'}), 400



# Endpoint para obtener la configuración actual
@app.route('/settings', methods=['GET'])
def get_settings():
    # Consulta para obtener la configuración desde la base de datos
    query = "SELECT api_key, model FROM settings"
    settings = gpt_manager.execute_query(query, fetchone=True)
    
    if settings:
        # Convierte los resultados de la base de datos en un diccionario
        config = {
            'api_key': settings['api_key'],
            'model': settings['model']
        }
    else:
        # Si no hay configuración en la base de datos, devuelve un mensaje adecuado
        config = {'message': 'No hay configuración disponible.'}
    
    return jsonify(config), 200


if __name__ == '__main__':
    app.run(debug=True)
