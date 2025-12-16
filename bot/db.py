import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT"))
    )

def register_request(user_id, nombre, correo, tipo_solicitud, detalle):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO requests (user_id, nombre, correo, tipo_solicitud, detalle)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (user_id, nombre, correo, tipo_solicitud, detalle))

    conn.commit()
    cursor.close()
    conn.close()
