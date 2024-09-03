import gpt_manager


class Flujo:
    def __init__(self, id=None, nombre=None):
        self.id = id
        self.nombre = nombre
        self.agentes = []

    @staticmethod
    def crear_flujo(nombre, agentes):
        # Primero, inserta el flujo sin la cláusula RETURNING
        gpt_manager.execute_query(
            "INSERT INTO Flujos (nombre) VALUES (%s)", 
            params=(nombre,)
        )

        # Recupera el ID del último flujo insertado
        flujo_id = gpt_manager.execute_query(
            "SELECT id FROM Flujos WHERE nombre = %s ORDER BY id DESC LIMIT 1", 
            params=(nombre,),
            fetchone=True
        )['id']

        for agente in agentes:
            gpt_id = agente['gpt_id']
            orden = agente['orden']
            prompt_entrada = agente.get('prompt_entrada', '')

            gpt_manager.execute_query(
                "INSERT INTO Flujo_Agentes (flujo_id, gpt_id, orden, prompt_entrada) VALUES (%s, %s, %s, %s)", 
                params=(flujo_id, gpt_id, orden, prompt_entrada)
            )

        return flujo_id



    def obtener_prompt_entrada(self, orden, respuesta_anterior=None, prompt_usuario=None):
        agente = next((a for a in self.agentes if a['orden'] == orden), None)
        if not agente:
            return None

        prompt_entrada_config = agente.get('prompt_entrada')
        if prompt_entrada_config == 'usuario':
            return prompt_usuario
        elif prompt_entrada_config == 'respuesta_anterior':
            return respuesta_anterior
        elif prompt_entrada_config == 'usuario_respuesta_anterior':
            return f"{prompt_usuario} {respuesta_anterior}"
        else:
            return agente.get('system')  # Default: usar el mensaje del sistema

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
            "SELECT gpt_id, orden, prompt_entrada FROM Flujo_Agentes WHERE flujo_id = %s ORDER BY orden", 
            params=(flujo_id,),
            fetchall=True
        )

        flujo.agentes = [{'gpt_id': row['gpt_id'], 'orden': row['orden'], 'prompt_entrada': row['prompt_entrada']} for row in agentes_data]
        return flujo
