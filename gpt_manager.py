from config import get_db_connection

def execute_query(query, params=(), fetchone=False, fetchall=False):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)  # Use dictionary=True if you want dict-like cursor
    cursor.execute(query, params)
    
    result = None
    if fetchone:
        result = cursor.fetchone()
    elif fetchall:
        result = cursor.fetchall()
    
    db.commit()
    cursor.close()
    db.close()
    
    return result

def create_gpt(name, api_key, model, system_message):
    query = """
        INSERT INTO gpts (name, api_key, model, system_message)
        VALUES (%s, %s, %s, %s)
    """
    params = (name, api_key, model, system_message)
    execute_query(query, params)

def update_gpt(gpt_id, name=None, api_key=None, model=None, system_message=None):
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
    if api_key:
        updates.append("api_key = %s")
        params.append(api_key)
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
