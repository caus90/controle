from connect import conectar_banco
from interface import iniciar_interface
from functions import on_text_change, abrir_relatorio, mostrar_status_carro, verificar_status_carro, toggle_fullscreen, atualizar_relogio
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    root, entry_codigo, label_mensagem, label_status_carro, label_relogio = iniciar_interface(
        lambda root, entry_codigo, label_mensagem, label_status_carro: on_text_change(root, entry_codigo, label_mensagem, label_status_carro),
        abrir_relatorio
    )
    
    root.attributes('-fullscreen', True)
    root.bind('<F11>', lambda event: toggle_fullscreen(root))

    atualizar_relogio(label_relogio)

    conn = conectar_banco()
    if conn:
        cursor = conn.cursor()
        status_carro, cor_status = verificar_status_carro(cursor)
        mostrar_status_carro(label_status_carro, status_carro, cor_status)
        cursor.close()
        conn.close()
    root.mainloop()
