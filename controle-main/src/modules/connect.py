import mysql.connector
from mysql.connector import Error
import os

def conectar_banco():
    try:
        conexao = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        if conexao.is_connected():
            return conexao
    except Error as e:
        print(f"Erro ao conectar no Banco de Dados: {e}")
        return None
