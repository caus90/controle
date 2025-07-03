import os
from datetime import datetime
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import PhotoImage
from PIL import Image, ImageTk
from functions import on_text_change, abrir_relatorio, mostrar_status_carro, verificar_status_carro, atualizar_relogio
from connect import conectar_banco

def iniciar_interface(on_text_change, abrir_relatorio):
    root = tk.Tk()
    root.state('zoomed')
    root.title("Controle de Veículos")

    script_dir = os.path.dirname(__file__)
    bg_image_path = os.path.join(script_dir, "..", "img", "logo.png")

    try:
        bg_image = Image.open(bg_image_path)
        bg_image = bg_image.resize((1141, 151), Image.Resampling.LANCZOS)
        bg_photo = ImageTk.PhotoImage(bg_image)
    except FileNotFoundError:
        print(f"Erro: A imagem {bg_image_path} não foi encontrada.")
        bg_photo = None

    if bg_photo:
        bg_label = tk.Label(root, image=bg_photo, bd=0)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=-0.3, relwidth=1, relheight=1)

    frame_principal = tk.Frame(root, padx=20, pady=20)
    frame_principal.place(relx=0.5, rely=0.5, anchor="center")

    label_instrucoes = tk.Label(frame_principal, text="Escaneie o código de barras:", font=("Arial", 26))
    label_instrucoes.pack(pady=(0, 10))

    entry_codigo = tk.StringVar()
    entry_codigo_widget = tk.Entry(frame_principal, textvariable=entry_codigo, font=("Arial", 18))
    entry_codigo_widget.pack(pady=(0, 10))
    
    label_mensagem = tk.Label(root, text="", font=("Arial", 22), fg="green")
    label_mensagem.place(relx=0.5, rely=0.7, anchor="center")

    label_status_carro = tk.Label(root, text="Status do carro", font=("Arial", 26), fg="black")
    label_status_carro.place(relx=0.5, rely=0.8, anchor="center")

    entry_codigo.trace_add("write", on_text_change(root, entry_codigo, label_mensagem, label_status_carro))

    botao_relatorio = tk.Button(root, bg="lightgray", text="Ver relatório", font=("Arial", 18), command=abrir_relatorio(root, entry_codigo, label_status_carro, label_mensagem))
    botao_relatorio.place(relx=0.01, rely=0.98, anchor='sw')

    label_relogio = tk.Label(root, text="", font=("Arial", 26))
    label_relogio.place(relx=0.98, rely=0.98, anchor='se')

    return root, entry_codigo, label_mensagem, label_status_carro, label_relogio
