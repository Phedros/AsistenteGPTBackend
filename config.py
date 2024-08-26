import mysql.connector # type: ignore

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="localgpt"
    )
