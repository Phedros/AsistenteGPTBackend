from config import get_db_connection
import mysql.connector

def execute_query(query, params=(), fetchone=False, fetchall=False):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)  # Use dictionary=True if you want dict-like cursor
        cursor.execute(query, params)
        
        result = None
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        
        db.commit()
        return result
    except mysql.connector.Error as e:
        print(f"Error al ejecutar la consulta: {e}")
    finally:
        cursor.close()
        db.close()

def fetch_query(query, params=(), fetchone=False, fetchall=False):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute(query, params)

        result = None
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()

        return result
    except mysql.connector.Error as e:
        print(f"Error al ejecutar la consulta: {e}")
    finally:
        cursor.close()
        db.close()



def create_gpt(name, model, system_message):
    query = """
        INSERT INTO gpts (name, model, system_message)
        VALUES (%s, %s, %s)
    """
    params = (name, model, system_message)
    execute_query(query, params)

def update_gpt(gpt_id, name=None, model=None, system_message=None):
    # Verificar si el nuevo nombre ya existe en otro GPT
    if name:
        name_exists_query = "SELECT id FROM gpts WHERE name = %s AND id != %s"
        result = execute_query(name_exists_query, (name, gpt_id), fetchone=True)
        if result:
            raise ValueError(f"El nombre '{name}' ya está en uso por otro GPT.")

    updates = []
    params = []

    if name:
        updates.append("name = %s")
        params.append(name)
    if model:
        updates.append("model = %s")
        params.append(model)
    if system_message:
        updates.append("system_message = %s")
        params.append(system_message)

    if updates:
        query = f"UPDATE gpts SET {', '.join(updates)} WHERE id = %s"
        params.append(gpt_id)
        execute_query(query, tuple(params))

def delete_gpt(gpt_id):
    query = "DELETE FROM gpts WHERE id = %s"
    execute_query(query, (gpt_id,))

def get_gpt_config(gpt_id):
    return execute_query("SELECT * FROM gpts WHERE id = %s", (gpt_id,), fetchone=True)

