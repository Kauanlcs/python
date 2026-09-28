import customtkinter as ctk
from tkinter import ttk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------- CADASTRO -----------------

produtos = {
    "7896590801225": ("Produto 1", 9.30),
    "7896005403259": ("Produto 2", 5.75),
    "7908279002684": ("Produto 3", 12.50),
}

total = 0

# --------------- JANELA --------------------

app = ctk.CTk()
app.geometry("900x550")
app.title("Mercado LF")

titulo = ctk.CTkLabel(
    app,
    text="🏪 MERCADO LF",
    font=("Arial",30,"bold")
)
titulo.pack(pady=10)

entrada = ctk.CTkEntry(app,width=400,font=("Arial",18))
entrada.pack(pady=10)
entrada.focus()

colunas=("Produto","Preço")

tabela=ttk.Treeview(app,columns=colunas,show="headings",height=12)

tabela.heading("Produto",text="Produto")
tabela.heading("Preço",text="Preço")

tabela.column("Produto",width=600)
tabela.column("Preço",width=150)

tabela.pack()

lblTotal=ctk.CTkLabel(
    app,
    text="TOTAL: R$ 0,00",
    font=("Arial",28,"bold")
)
lblTotal.pack(pady=20)


def ler(event=None):
    global total

    codigo=entrada.get().strip()

    entrada.delete(0,"end")

    if codigo in produtos:

        nome,preco=produtos[codigo]

        tabela.insert(
            "",
            "end",
            values=(nome,f"R$ {preco:.2f}")
        )

        total+=preco

        lblTotal.configure(
            text=f"TOTAL: R$ {total:.2f}"
        )

    else:

        tabela.insert(
            "",
            "end",
            values=("PRODUTO NÃO CADASTRADO","")
        )


entrada.bind("<Return>",ler)

def limpar():

    global total

    for i in tabela.get_children():
        tabela.delete(i)

    total=0

    lblTotal.configure(text="TOTAL: R$ 0,00")


ctk.CTkButton(
    app,
    text="Nova Compra",
    command=limpar,
    width=200
).pack(pady=10)

app.mainloop()