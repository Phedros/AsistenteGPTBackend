import json
from config import get_db_connection
import gpt_manager
import mysql.connector


class Flujo:
    def __init__(self, id=None, nombre=None):
        self.id = id
        self.nombre = nombre
        self.agentes = []

    @staticmethod
    def crear_flujo(nombre, agentes):
        # Inserta el flujo en la tabla `Flujos`
        gpt_manager.execute_query(
            "INSERT INTO Flujos (nombre) VALUES (%s)", 
            params=(nombre,)
        )

        # Recupera el ID del flujo recién creado
        flujo_id = gpt_manager.execute_query(
            "SELECT id FROM Flujos WHERE nombre = %s ORDER BY id DESC LIMIT 1", 
            params=(nombre,),
            fetchone=True
        )['id']

        # Itera sobre los agentes proporcionados en el cuerpo de la solicitud
        for agente in agentes:
            gpt_id = agente['gpt_id']
            orden = agente['orden']
            prompt_entrada = agente.get('prompt_entrada', '')
            tipo_prompt = agente.get('tipo_prompt')
            referencias_respuestas = json.dumps(agente.get('referencias_respuestas', []))  # Convertir a JSON para almacenar múltiples referencias
            incluir_prompt_usuario = agente.get('incluir_prompt_usuario', False)

            # Inserta cada agente del flujo en la tabla `Flujo_Agentes`
            gpt_manager.execute_query(
                """
                INSERT INTO Flujo_Agentes (flujo_id, gpt_id, orden, prompt_entrada, tipo_prompt, referencias_respuestas, incluir_prompt_usuario)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, 
                params=(flujo_id, gpt_id, orden, prompt_entrada, tipo_prompt, referencias_respuestas, incluir_prompt_usuario)
            )

        return flujo_id
    
    @staticmethod
    def eliminar_flujo(flujo_id):
        """
        Elimina un flujo y todos sus agentes y el historial de conversación asociado.
        
        :param flujo_id: ID del flujo a eliminar.
        :return: True si la eliminación fue exitosa, False en caso contrario.
        """
        # Primero, eliminar el historial de conversación asociado al flujo
        delete_history_query = "DELETE FROM flujo_conversation_history WHERE flujo_id = %s"
        
        # Segundo, eliminar los agentes asociados al flujo
        delete_agents_query = "DELETE FROM Flujo_Agentes WHERE flujo_id = %s"
        
        # Finalmente, eliminar el flujo
        delete_flujo_query = "DELETE FROM Flujos WHERE id = %s"
        
        try:
            db = get_db_connection()
            cursor = db.cursor()
            
            # Ejecutar las consultas en el orden correcto
            cursor.execute(delete_history_query, (flujo_id,))
            cursor.execute(delete_agents_query, (flujo_id,))
            cursor.execute(delete_flujo_query, (flujo_id,))
            
            db.commit()
            return True
        except mysql.connector.Error as e:
            print(f"Error al eliminar el flujo: {e}")
            return False
        finally:
            cursor.close()
            db.close()



    def obtener_prompt_entrada(self, orden, respuestas_anteriores=None, prompt_usuario=None):
        agente = next((a for a in self.agentes if a['orden'] == orden), None)
        if not agente:
            return None

        tipo_prompt = agente.get('tipo_prompt')

        if tipo_prompt == 'usuario':
            return prompt_usuario
        elif tipo_prompt == 'respuesta_anterior':
            referencia = agente.get('referencias_respuestas', [])[0]  # Tomar la primera referencia si existe
            return respuestas_anteriores.get(referencia)
        elif tipo_prompt == 'combinado':
            prompt_entrada = ""
            # Combinar todas las respuestas referenciadas
            for referencia in agente.get('referencias_respuestas', []):
                if referencia in respuestas_anteriores:
                    prompt_entrada += f"{respuestas_anteriores[referencia]} "

            # Incluir el prompt del usuario si está especificado
            if agente.get('incluir_prompt_usuario', False):
                prompt_entrada = f"{prompt_usuario} {prompt_entrada}"

            return prompt_entrada.strip()
        else:  # 'system' or cualquier otro caso
            return agente.get('system', '')  # Default: usar el mensaje del sistema


    @staticmethod
    def obtener_flujo_por_id(flujo_id):
        flujo_data = gpt_manager.execute_query(
            "SELECT id, nombre FROM Flujos WHERE id = %s", 
            params=(flujo_id,), 
            fetchone=True
        )

        if not flujo_data:
            return None
        
        flujo = Flujo(id=flujo_data['id'], nombre=flujo_data['nombre'])

        agentes_data = gpt_manager.execute_query(
            """
            SELECT gpt_id, orden, prompt_entrada, tipo_prompt, referencias_respuestas, incluir_prompt_usuario 
            FROM Flujo_Agentes 
            WHERE flujo_id = %s 
            ORDER BY orden
            """, 
            params=(flujo_id,),
            fetchall=True
        )

        flujo.agentes = [
            {
                'gpt_id': row['gpt_id'],
                'orden': row['orden'],
                'prompt_entrada': row['prompt_entrada'],
                'tipo_prompt': row['tipo_prompt'],
                'referencias_respuestas': json.loads(row['referencias_respuestas']) if row['referencias_respuestas'] else [],
                'incluir_prompt_usuario': row['incluir_prompt_usuario']
            }
            for row in agentes_data
        ]
        
        return flujo

    
    @staticmethod
    def crear_conversacion_flujo(flujo_id, empty_history):
        """
        Crea una nueva conversación para un flujo y guarda un historial vacío.
        
        :param flujo_id: ID del flujo para el cual se crea la conversación.
        :param empty_history: Historial vacío para inicializar la conversación.
        :return: ID de la nueva conversación en el flujo.
        """
        query = """
            INSERT INTO flujo_conversation_history (flujo_id, conversation_json)
            VALUES (%s, %s)
        """
        params = (flujo_id, empty_history)
        
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute(query, params)
            
            # Obtener el ID de la nueva conversación del flujo utilizando lastrowid
            flujo_conversation_id = cursor.lastrowid
            
            db.commit()
            return flujo_conversation_id
        except mysql.connector.Error as e:
            print(f"Error al crear la conversación del flujo: {e}")
            return None
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def conversacion_existe(flujo_conversation_id):
        """
        Verifica si una conversación de flujo existe en la base de datos.
        
        :param flujo_conversation_id: ID de la conversación del flujo.
        :return: True si existe, False en caso contrario.
        """
        flujo_conversation = gpt_manager.execute_query(
            "SELECT id FROM flujo_conversation_history WHERE id = %s", 
            params=(flujo_conversation_id,), 
            fetchone=True
        )
        return flujo_conversation is not None

    @staticmethod
    def eliminar_conversacion_flujo(flujo_conversation_id):
        """
        Elimina una conversación específica de un flujo.
        
        :param flujo_conversation_id: ID de la conversación del flujo a eliminar.
        :return: True si la eliminación fue exitosa, False en caso contrario.
        """
        query = "DELETE FROM flujo_conversation_history WHERE id = %s"
        params = (flujo_conversation_id,)
        
        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute(query, params)
            
            # Confirmar que se eliminó exactamente una fila
            if cursor.rowcount == 1:
                db.commit()
                return True
            else:
                return False
        except mysql.connector.Error as e:
            print(f"Error al eliminar la conversación del flujo: {e}")
            return False
        finally:
            cursor.close()
            db.close()


    @staticmethod
    def obtener_historial_flujo(conversation_id):
        """
        Obtiene el historial de conversación de un flujo en formato JSON.
        
        :param flujo_id: ID del flujo.
        :return: Historial de conversación como lista de diccionarios.
        """
        query = "SELECT conversation_json FROM flujo_conversation_history WHERE id = %s"
        result = gpt_manager.fetch_query(query, (conversation_id,), fetchone=True)
        
        if result and result['conversation_json']:
            return json.loads(result['conversation_json'])  # Convertir JSON a lista de diccionarios
        
        return []

    @staticmethod
    def actualizar_historial_flujo(flujo_id, conversation_history):
        """
        Actualiza el historial de conversación de un flujo en la base de datos.
        
        :param flujo_id: ID del flujo.
        :param conversation_history: Historial completo de la conversación del flujo.
        """
        query = """
            UPDATE flujo_conversation_history
            SET conversation_json = %s
            WHERE flujo_id = %s
        """
        params = (json.dumps(conversation_history), flujo_id)
        
        gpt_manager.execute_query(query, params)

    @staticmethod
    def obtener_agentes_por_flujo(flujo_id):
        """
        Obtiene todos los agentes de un flujo por su ID.
        """
        query = """
            SELECT gpt_id, orden, prompt_entrada, tipo_prompt 
            FROM Flujo_Agentes 
            WHERE flujo_id = %s 
            ORDER BY orden
        """
        params = (flujo_id,)
        return gpt_manager.execute_query(query, params, fetchall=True)
    
    @staticmethod
    def obtener_todos_flujos():
        """
        Obtiene todos los flujos de la base de datos.
        """
        query = "SELECT id, nombre FROM Flujos"
        flujos = gpt_manager.execute_query(query, fetchall=True)
        return flujos
    
    @staticmethod
    def obtener_conversaciones_por_flujo(flujo_id):
        """
        Obtiene todas las conversaciones asociadas a un flujo específico por su ID.
        
        :param flujo_id: ID del flujo para el cual se quieren obtener las conversaciones.
        :return: Lista de conversaciones en formato de diccionarios.
        """
        query = """
            SELECT id, conversation_json 
            FROM flujo_conversation_history 
            WHERE flujo_id = %s
        """
        params = (flujo_id,)
        conversaciones = gpt_manager.execute_query(query, params, fetchall=True)
        
        # Devolver las conversaciones en un formato más amigable (sin el JSON crudo)
        conversaciones_format = [
            {
                "id": conversacion['id'],
                "conversation": json.loads(conversacion['conversation_json']) if conversacion['conversation_json'] else []
            }
            for conversacion in conversaciones
        ]
        
        return conversaciones_format

    @staticmethod
    def obtener_historial_conversacion(flujo_id, conversation_id):
        """
        Obtiene el historial de conversación de un flujo específico.
        
        :param flujo_id: ID del flujo.
        :param conversation_id: ID de la conversación dentro del flujo.
        :return: Historial de conversación como lista de diccionarios.
        """
        query = """
            SELECT conversation_json 
            FROM flujo_conversation_history 
            WHERE flujo_id = %s AND id = %s
        """
        params = (flujo_id, conversation_id)
        result = gpt_manager.execute_query(query, params, fetchone=True)
        
        if result and result['conversation_json']:
            return json.loads(result['conversation_json'])  # Convertir JSON a lista de diccionarios
        
        return []
