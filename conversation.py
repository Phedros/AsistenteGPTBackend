from config import get_db_connection
import json
import mysql.connector

def save_conversation(gpt_id, conversation_history):
    """
    Guarda el historial completo de la conversación en formato JSON.
    """
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO conversation_history (gpt_id, conversation_json)
            VALUES (%s, %s)
        """, (gpt_id, json.dumps(conversation_history)))  # Convertir la lista a JSON
        db.commit()
    except mysql.connector.Error as e:
        print(f"Error al guardar la conversación: {e}")
    finally:
        cursor.close()
        db.close()

def get_conversation_history(gpt_id):
    """
    Obtiene el historial completo de la conversación en formato JSON.
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT conversation_json
            FROM conversation_history
            WHERE gpt_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (gpt_id,))
        record = cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Error al obtener el historial de conversación: {e}")
        return []
    finally:
        cursor.close()
        db.close()
    
    if record and record['conversation_json']:
        return json.loads(record['conversation_json'])  # Convertir JSON a lista
    return []

def delete_conversation_history(gpt_id):
    """
    Elimina el historial de conversación para un GPT específico.
    
    :param gpt_id: ID del GPT cuyo historial debe ser eliminado.
    """
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("DELETE FROM conversation_history WHERE gpt_id = %s", (gpt_id,))
        db.commit()
    except mysql.connector.Error as e:
        print(f"Error al eliminar el historial de conversación: {e}")
    finally:
        cursor.close()
        db.close()
