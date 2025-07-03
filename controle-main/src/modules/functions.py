import mysql.connector
from connect import conectar_banco
from datetime import datetime, timedelta
import tkinter as tk
import tkinter.ttk as ttk

ultima_leitura = None
leitura_em_progresso = False
temporizador_debounce = None
temporizador_mensagem = None

def on_text_change(root, entry_codigo, label_mensagem, label_status_carro):
    def callback(*args):
        global ultima_leitura, leitura_em_progresso, temporizador_debounce

        if leitura_em_progresso:
            return
        
        leitura_em_progresso = True

        if temporizador_debounce:
            root.after_cancel(temporizador_debounce)
        
        def processa_leitura():
            global ultima_leitura, leitura_em_progresso

            barcode = entry_codigo.get().strip()
            if barcode and len(barcode) == 6:
                now = datetime.now()
                if ultima_leitura is None or now - ultima_leitura > timedelta(seconds=10):
                    ultima_leitura = now
                    conn = conectar_banco()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            resultado, cor_mensagem = registrar_acao(cursor, barcode)
                            mostrar_mensagem_temporaria(root, label_mensagem, entry_codigo, resultado, cor_mensagem)
                            status_carro, cor_status = verificar_status_carro(cursor)
                            mostrar_status_carro(label_status_carro, status_carro, cor_status)
                            conn.commit()
                        except mysql.connector.Error as err:
                            mostrar_mensagem_temporaria(root, label_mensagem, entry_codigo, f"Erro: {err}", "red")
                        finally:
                            cursor.close()
                            conn.close()
                else:
                    mostrar_mensagem_temporaria(root, label_mensagem, entry_codigo, "Aguarde antes de ler outro código.", "red")
            leitura_em_progresso = False
        temporizador_debounce = root.after(100, processa_leitura)
    return callback

def abrir_relatorio(root, entry_codigo, label_status_carro, label_mensagem):
    def callback():
        nova_tela = tk.Toplevel(root)
        nova_tela.title("Relatório")
        nova_tela.geometry("800x600")

        label = tk.Label(nova_tela, text="Relatório dos 10 últimos usos", font=("Arial", 16))
        label.pack(pady=10)

        conn = conectar_banco()
        if conn:
            cursor = conn.cursor()
            try:
                ultimos_usos = buscar_ultimos_usos(cursor)

                columns = ("nome", "tipo", "data_hora")
                tree = ttk.Treeview(nova_tela, columns=columns, show="headings")

                tree.heading("nome", text="Nome", anchor=tk.W)
                tree.heading("tipo", text="Tipo", anchor=tk.W)
                tree.heading("data_hora", text="Data e Hora", anchor=tk.W)

                tree.column("nome", width=200, anchor=tk.W)
                tree.column("tipo", width=100, anchor=tk.W)
                tree.column("data_hora", width=200, anchor=tk.W)

                style = ttk.Style()
                style.configure("Treeview.Heading", font=("Arial", 12))
                style.configure("Treeview", rowheight=30)

                tree.tag_configure("saida", background="white", font=("Arial", 14))
                tree.tag_configure("volta", background="lightgray", font=("Arial", 14))

                for uso in ultimos_usos:
                    nome = uso[0]
                    tipo = uso[1]
                    data_hora = uso[2].strftime("%d/%m/%Y %H:%M")
                    if tipo == "saída":
                        tree.insert("", tk.END, values=(nome, tipo, data_hora), tags=("saida",))
                    elif tipo == "volta":
                        tree.insert("", tk.END, values=(nome, tipo, data_hora), tags=("volta",))

                tree.pack(pady=10, expand=True, fill="both")

            except mysql.connector.Error as err:
                tk.Label(nova_tela, text=f"Erro: {err}", fg="red", font=("Arial", 14)).pack(pady=10)
            finally:
                cursor.close()
                conn.close()
    return callback

def mostrar_status_carro(label_status_carro, status, cor):
    label_status_carro.config(text=status, fg=cor)

def verificar_status_carro(cursor):
    cursor.execute("""
        SELECT p.nome, r.tipo
        FROM Registros r
        JOIN Pessoa p ON r.pessoa_id = p.id
        WHERE r.tipo = 'saída'
        AND NOT EXISTS (
            SELECT 1 FROM Registros r2
            WHERE r2.tipo = 'volta' AND r2.pessoa_id = r.pessoa_id AND r2.data_hora > r.data_hora
        )
    """)
    registro = cursor.fetchone()
    if registro:
        nome = registro[0]
        return f"O carro está sendo usado por {nome}.", "black"
    else:
        return "O carro está livre!", "black"

def verificar_saida_pendente(cursor):
    cursor.execute("""
        SELECT pessoa_id FROM Registros r1
        WHERE r1.tipo = 'saída' 
        AND NOT EXISTS (
            SELECT 1 FROM Registros r2
            WHERE r2.tipo = 'volta' AND r2.pessoa_id = r1.pessoa_id AND r2.data_hora > r1.data_hora
        )
    """)
    return cursor.fetchall()

def obter_saudacao():
    hora_atual = datetime.now().hour
    if hora_atual < 12:
        return "Muito bom dia"
    elif hora_atual < 18:
        return "Muito boa tarde"
    else:
        return "Muito boa noite"

def registrar_acao(cursor, barcode):
    saudacao = obter_saudacao()
    cursor.execute("SELECT * FROM Pessoa WHERE barcode=%s", (barcode,))
    pessoa = cursor.fetchone()

    if pessoa:
        nome = pessoa[1]
        pessoa_id = pessoa[0]
        data_hora = datetime.now()
        data = datetime.now()
        hora = datetime.now()
        data_formatada = data.strftime("%d/%m/%y")
        hora_formatada = hora.strftime("%H:%M")

        saidas_pendentes = verificar_saida_pendente(cursor)

        for saida in saidas_pendentes:
            if saida[0] != pessoa_id:
                cursor.execute("SELECT nome FROM Pessoa WHERE id=%s", (saida[0],))
                nome_pendente = cursor.fetchone()[0]
                return f"{saudacao}, {nome}. Registro bloqueado! {nome_pendente} ainda não retornou. Aguarde o registro da volta antes de registrar outra saída.", "red"

        cursor.execute("SELECT tipo FROM Registros WHERE pessoa_id=%s ORDER BY data_hora DESC LIMIT 1", (pessoa_id,))
        ultima_acao = cursor.fetchone()

        if ultima_acao is None:
            tipo = "saída"
            mensagem_final = f"{saudacao}, {nome}. Registro de {tipo} realizado com sucesso em {data_formatada} às {hora_formatada}. Tenha um bom trabalho!"
            cor_mensagem = "green"
        elif ultima_acao[0] == "saída":
            tipo = "volta"
            mensagem_final = f"{saudacao}, {nome}. Registro de {tipo} realizado com sucesso em {data_formatada} às {hora_formatada}. Tenha um bom trabalho!"
            cor_mensagem = "blue"
        elif ultima_acao[0] == "volta":
            tipo = "saída"
            mensagem_final = f"{saudacao}, {nome}. Registro de {tipo} realizado com sucesso em {data_formatada} às {hora_formatada}. Tenha um bom trabalho!"
            cor_mensagem = "green"

        cursor.execute("INSERT INTO Registros (pessoa_id, data_hora, tipo) VALUES (%s, %s, %s)", (pessoa_id, data_hora, tipo))
        return mensagem_final, cor_mensagem
    else:
        return f"{saudacao}. Pessoa não encontrada!", "black"

def mostrar_mensagem_temporaria(root, label_mensagem, entry_codigo, mensagem, cor):
    global temporizador_mensagem
    if temporizador_mensagem:
        root.after_cancel(temporizador_mensagem)
    label_mensagem.config(text=mensagem, fg=cor)
    temporizador_mensagem = root.after(15000, lambda: limpar_mensagem(label_mensagem))
    root.after(100, lambda: limpar_campo(entry_codigo))

def limpar_mensagem(label_mensagem):
    label_mensagem.config(text="")

def limpar_campo(entry_codigo):
    entry_codigo.set("")

def buscar_ultimos_usos(cursor):
    cursor.execute("""
        SELECT p.nome, r.tipo, r.data_hora
        FROM Registros r
        JOIN Pessoa p ON r.pessoa_id = p.id
        ORDER BY r.data_hora DESC
        LIMIT 20
    """)
    return cursor.fetchall()

def atualizar_relogio(label_relogio):
    agora = datetime.now().strftime("%H:%M")
    label_relogio.config(text=agora)
    label_relogio.after(1000, atualizar_relogio, label_relogio)

def toggle_fullscreen(root):
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))
