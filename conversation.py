from config import get_db_connection
import json
import mysql.connector

def save_conversation(conversation_id, conversation_history):
    """
    Guarda o actualiza el historial completo de la conversación en formato JSON usando el ID de la conversación.
    """
    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Verificar si ya existe un historial para el conversation_id
        cursor.execute("SELECT COUNT(*) FROM conversation_history WHERE id = %s", (conversation_id,))
        count = cursor.fetchone()[0]

        if count > 0:
            # Si existe, actualizar el historial existente
            cursor.execute("""
                UPDATE conversation_history
                SET conversation_json = %s
                WHERE id = %s
            """, (json.dumps(conversation_history), conversation_id))
        else:
            # Si no existe, insertar un nuevo historial
            cursor.execute("""
                INSERT INTO conversation_history (gpt_id, conversation_json)
                VALUES (%s, %s)
            """, (gpt_id, json.dumps(conversation_history)))

        db.commit()
    except mysql.connector.Error as e:
        print(f"Error al guardar la conversación: {e}")
    finally:
        cursor.close()
        db.close()



def get_conversation_history(conversation_id):
    """
    Obtiene el historial completo de la conversación en formato JSON usando el ID de la conversación.
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT conversation_json
            FROM conversation_history
            WHERE id = %s
        """, (conversation_id,))
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

def delete_conversation_history(conversation_id):
    """
    Elimina el historial de conversación para un ID de conversación específico.
    
    :param conversation_id: ID de la conversación que debe ser eliminada.
    """
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("DELETE FROM conversation_history WHERE id = %s", (conversation_id,))
        db.commit()
    except mysql.connector.Error as e:
        print(f"Error al eliminar el historial de conversación: {e}")
    finally:
        cursor.close()
        db.close()

def create_conversation(gpt_id):
    """
    Crea una nueva conversación para un GPT específico y devuelve el ID de la nueva conversación.
    
    :param gpt_id: ID del GPT para el cual se crea la conversación.
    :return: ID de la nueva conversación.
    """
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Insertar una nueva conversación con un historial vacío
        cursor.execute("""
            INSERT INTO conversation_history (gpt_id, conversation_json)
            VALUES (%s, %s)
        """, (gpt_id, json.dumps([])))  # Inicializa el historial como una lista vacía

        # Obtener el ID de la nueva conversación
        conversation_id = cursor.lastrowid

        db.commit()
        return conversation_id
    except mysql.connector.Error as e:
        print(f"Error al crear la nueva conversación: {e}")
        return None
    finally:
        cursor.close()
        db.close()

def get_all_conversations(gpt_id):
    """
    Obtiene todas las conversaciones asociadas con un GPT específico.
    
    :param gpt_id: ID del GPT para el cual se obtienen las conversaciones.
    :return: Lista de diccionarios con los IDs de conversación.
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT id FROM conversation_history WHERE gpt_id = %s
        """, (gpt_id,))
        records = cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Error al obtener las conversaciones: {e}")
        return []
    finally:
        cursor.close()
        db.close()

    return [{'id': record['id']} for record in records]



