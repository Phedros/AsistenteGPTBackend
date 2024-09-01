import gpt_manager


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

    # Puedes agregar más métodos según lo necesites
