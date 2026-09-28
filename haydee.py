import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

PASTA = os.path.dirname(os.path.abspath(__file__))
con = sqlite3.connect(os.path.join(PASTA, "haydee.db"))
con.executescript("""
CREATE TABLE IF NOT EXISTS produtos(codigo TEXT PRIMARY KEY, nome TEXT NOT NULL,
    preco REAL NOT NULL, estoque INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS vendas(id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT,
    total REAL, pagamento TEXT);
CREATE TABLE IF NOT EXISTS itens(venda_id INTEGER, codigo TEXT, nome TEXT,
    preco REAL, qtd INTEGER);
""")

VERDE, AMARELO, VERMELHO = "#14532d", "#f2c230", "#d6402b"


def r(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


root = tk.Tk()
root.title("Supermercado Haydée")
root.geometry("1050x680")
root.minsize(900, 600)

# ---------------- Cabeçalho ----------------
topo = tk.Frame(root, bg=VERDE)
topo.pack(fill="x")
try:
    _img = tk.PhotoImage(file=os.path.join(PASTA, "logo.png"))
    _img = _img.subsample(max(1, _img.width() // 48))
    tk.Label(topo, image=_img, bg=VERDE).pack(side="left", padx=(12, 6), pady=8)
except tk.TclError:
    pass
tk.Label(topo, text="Supermercado Haydée", bg=VERDE, fg="white",
         font=("Segoe UI", 20, "bold")).pack(side="left", pady=8)

abas = ttk.Notebook(root)
abas.pack(fill="both", expand=True, padx=8, pady=8)
aba_caixa, aba_prod, aba_vend = tk.Frame(abas), tk.Frame(abas), tk.Frame(abas)
abas.add(aba_caixa, text="  Caixa  ")
abas.add(aba_prod, text="  Produtos  ")
abas.add(aba_vend, text="  Vendas  ")


def botao(pai, texto, cmd, cor=VERDE, **kw):
    return tk.Button(pai, text=texto, command=cmd, bg=cor, fg="white",
                     activebackground=cor, relief="flat", cursor="hand2",
                     font=("Segoe UI", 11, "bold"), padx=12, pady=6, **kw)


# ---------------- Diálogo de produto ----------------
def dialogo_produto(codigo="", editar=False, depois=None, aviso=""):
    d = tk.Toplevel(root)
    d.title("Produto")
    d.transient(root)
    d.grab_set()
    if aviso:
        tk.Label(d, text=aviso, fg=VERMELHO, font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(12, 0))
    campos = {}
    rotulos = [("Código de barras", "codigo"), ("Nome", "nome"),
               ("Preço", "preco"), ("Estoque", "estoque")]
    for i, (rot, chave) in enumerate(rotulos, start=1):
        tk.Label(d, text=rot).grid(row=i, column=0, sticky="e", padx=8, pady=6)
        e = tk.Entry(d, width=32, font=("Segoe UI", 12))
        e.grid(row=i, column=1, padx=8, pady=6)
        campos[chave] = e
    campos["codigo"].insert(0, codigo)
    if editar:
        n, p, est = con.execute(
            "SELECT nome,preco,estoque FROM produtos WHERE codigo=?", (codigo,)).fetchone()
        campos["nome"].insert(0, n)
        campos["preco"].insert(0, str(p).replace(".", ","))
        campos["estoque"].insert(0, str(est))
        campos["codigo"].config(state="disabled")
    (campos["nome"] if codigo else campos["codigo"]).focus_set()
    campos["codigo"].bind("<Return>", lambda e: campos["nome"].focus_set())

    def salvar():
        try:
            cod = campos["codigo"].get().strip()
            nome = campos["nome"].get().strip()
            preco = float(campos["preco"].get().replace(",", "."))
            est = int(campos["estoque"].get() or 0)
            assert cod and nome
        except Exception:
            messagebox.showerror("Erro", "Preencha código, nome e preço com valores válidos.", parent=d)
            return
        if editar:
            con.execute("UPDATE produtos SET nome=?,preco=?,estoque=? WHERE codigo=?",
                        (nome, preco, est, cod))
        else:
            if con.execute("SELECT 1 FROM produtos WHERE codigo=?", (cod,)).fetchone():
                messagebox.showerror("Erro", "Esse código já está cadastrado.", parent=d)
                return
            con.execute("INSERT INTO produtos VALUES(?,?,?,?)", (cod, nome, preco, est))
        con.commit()
        d.destroy()
        atualizar_produtos()
        if depois:
            depois(cod)
        scan.focus_set()

    linha = tk.Frame(d)
    linha.grid(row=5, column=0, columnspan=2, pady=12)
    botao(linha, "Salvar produto", salvar).pack(side="left", padx=6)
    botao(linha, "Cancelar", d.destroy, "#6b7a71").pack(side="left", padx=6)
    d.bind("<Return>", lambda e: salvar() if e.widget is not campos["codigo"] else None)


# ---------------- CAIXA ----------------
carrinho = {}  # codigo -> [nome, preco, qtd]

esq = tk.Frame(aba_caixa)
esq.pack(side="left", fill="both", expand=True, padx=(8, 4), pady=8)
dire = tk.Frame(aba_caixa, width=300)
dire.pack(side="right", fill="y", padx=(4, 8), pady=8)

tk.Label(esq, text="Passe o produto no leitor (ou digite o código e Enter):",
         font=("Segoe UI", 11)).pack(anchor="w")
scan = tk.Entry(esq, font=("Segoe UI", 22), relief="solid", bd=2,
                highlightthickness=2, highlightcolor=VERDE)
scan.pack(fill="x", pady=6)

cols = ("nome", "preco", "qtd", "sub")
tree = ttk.Treeview(esq, columns=cols, show="headings", height=14)
for c, t, w in zip(cols, ("Produto", "Preço", "Qtd", "Subtotal"), (330, 100, 60, 110)):
    tree.heading(c, text=t)
    tree.column(c, width=w, anchor="w" if c == "nome" else "e")
tree.pack(fill="both", expand=True)

acoes = tk.Frame(esq)
acoes.pack(fill="x", pady=6)

lbl_total = tk.Label(dire, text="R$ 0,00", font=("Segoe UI", 34, "bold"), fg=VERDE)
tk.Label(dire, text="Total da compra", font=("Segoe UI", 12)).pack(anchor="w")
lbl_total.pack(anchor="w", pady=(0, 10))
tk.Label(dire, text="Forma de pagamento").pack(anchor="w")
pagamento = tk.StringVar(value="Dinheiro")
combo = ttk.Combobox(dire, textvariable=pagamento, state="readonly",
                     values=("Dinheiro", "Cartão", "Pix"), font=("Segoe UI", 12))
combo.pack(fill="x", pady=(0, 10))
tk.Label(dire, text="Valor recebido").pack(anchor="w")
recebido = tk.StringVar()
ent_rec = tk.Entry(dire, textvariable=recebido, font=("Segoe UI", 16))
ent_rec.pack(fill="x")
lbl_troco = tk.Label(dire, text="", font=("Segoe UI", 16, "bold"), fg="#2ea15f")
lbl_troco.pack(anchor="w", pady=10)


def total():
    return sum(p * q for _, p, q in carrinho.values())


def calc_troco(*_):
    dinheiro = pagamento.get() == "Dinheiro"
    ent_rec.config(state="normal" if dinheiro else "disabled")
    if not dinheiro:
        lbl_troco.config(text="")
        return
    try:
        v = float(recebido.get().replace(",", "."))
    except ValueError:
        lbl_troco.config(text="")
        return
    t = total()
    lbl_troco.config(text=("Troco: " + r(v - t)) if v >= t else ("Falta: " + r(t - v)),
                     fg="#2ea15f" if v >= t else VERMELHO)


def atualizar():
    tree.delete(*tree.get_children())
    for cod, (nome, preco, qtd) in carrinho.items():
        tree.insert("", "end", iid=cod, values=(nome, r(preco), qtd, r(preco * qtd)))
    lbl_total.config(text=r(total()))
    calc_troco()


def adicionar(cod):
    row = con.execute("SELECT nome,preco,estoque FROM produtos WHERE codigo=?", (cod,)).fetchone()
    if not row:
        root.bell()
        dialogo_produto(cod, depois=adicionar, aviso="Produto não cadastrado. Cadastre agora:")
        return
    nome, preco, est = row
    atual = carrinho[cod][2] if cod in carrinho else 0
    if atual + 1 > est:
        root.bell()
        messagebox.showwarning("Estoque", f"Sem estoque suficiente de {nome} (restam {est}).")
        scan.focus_set()
        return
    if cod in carrinho:
        carrinho[cod][2] += 1
    else:
        carrinho[cod] = [nome, preco, 1]
    atualizar()
    scan.focus_set()


def ao_escanear(_=None):
    cod = scan.get().strip()
    scan.delete(0, "end")
    if cod:
        adicionar(cod)


def mais():
    if tree.selection():
        adicionar(tree.selection()[0])
    scan.focus_set()


def menos():
    if tree.selection():
        cod = tree.selection()[0]
        carrinho[cod][2] -= 1
        if carrinho[cod][2] < 1:
            del carrinho[cod]
        atualizar()
    scan.focus_set()


def remover():
    if tree.selection():
        del carrinho[tree.selection()[0]]
        atualizar()
    scan.focus_set()


def limpar():
    carrinho.clear()
    recebido.set("")
    atualizar()
    scan.focus_set()


def finalizar():
    if not carrinho:
        messagebox.showinfo("Caixa", "Adicione produtos antes de finalizar.")
        scan.focus_set()
        return
    t, troco = total(), 0
    if pagamento.get() == "Dinheiro":
        try:
            rec = float(recebido.get().replace(",", "."))
        except ValueError:
            rec = 0
        if rec < t:
            messagebox.showerror("Pagamento", "Valor recebido menor que o total.")
            return
        troco = rec - t
    cur = con.execute("INSERT INTO vendas(data,total,pagamento) VALUES(?,?,?)",
                      (datetime.now().isoformat(timespec="seconds"), t, pagamento.get()))
    for cod, (nome, preco, qtd) in carrinho.items():
        con.execute("INSERT INTO itens VALUES(?,?,?,?,?)", (cur.lastrowid, cod, nome, preco, qtd))
        con.execute("UPDATE produtos SET estoque=MAX(0,estoque-?) WHERE codigo=?", (qtd, cod))
    con.commit()
    messagebox.showinfo("Venda concluída",
                        f"Total: {r(t)}" + (f"\nTroco: {r(troco)}" if troco else ""))
    limpar()


botao(acoes, "＋", mais).pack(side="left", padx=2)
botao(acoes, "−", menos).pack(side="left", padx=2)
botao(acoes, "Remover item", remover, VERMELHO).pack(side="left", padx=8)
botao(dire, "Finalizar venda (F2)", finalizar).pack(fill="x", pady=(10, 4))
botao(dire, "Limpar (Esc)", limpar, "#6b7a71").pack(fill="x")

scan.bind("<Return>", ao_escanear)
pagamento.trace_add("write", calc_troco)
recebido.trace_add("write", calc_troco)
root.bind("<F2>", lambda e: finalizar())
root.bind("<Escape>", lambda e: limpar())

# ---------------- PRODUTOS ----------------
barra = tk.Frame(aba_prod)
barra.pack(fill="x", padx=8, pady=8)
busca = tk.StringVar()
tk.Entry(barra, textvariable=busca, font=("Segoe UI", 12)).pack(side="left", fill="x", expand=True)
tk.Label(barra, text=" ← buscar por nome ou código  ").pack(side="left")

pcols = ("codigo", "nome", "preco", "estoque")
tp = ttk.Treeview(aba_prod, columns=pcols, show="headings")
for c, t, w in zip(pcols, ("Código", "Produto", "Preço", "Estoque"), (160, 380, 110, 90)):
    tp.heading(c, text=t)
    tp.column(c, width=w, anchor="w" if c in ("codigo", "nome") else "e")
tp.tag_configure("baixo", foreground=VERMELHO)
tp.pack(fill="both", expand=True, padx=8)


def atualizar_produtos(*_):
    tp.delete(*tp.get_children())
    f = f"%{busca.get()}%"
    for cod, nome, preco, est in con.execute(
            "SELECT codigo,nome,preco,estoque FROM produtos WHERE nome LIKE ? OR codigo LIKE ? ORDER BY nome",
            (f, f)):
        tp.insert("", "end", iid=cod, values=(cod, nome, r(preco), est),
                  tags=("baixo",) if est <= 5 else ())


def editar_sel(_=None):
    if tp.selection():
        dialogo_produto(tp.selection()[0], editar=True)


def excluir_sel():
    if tp.selection() and messagebox.askyesno("Excluir", "Excluir o produto selecionado?"):
        con.execute("DELETE FROM produtos WHERE codigo=?", (tp.selection()[0],))
        con.commit()
        atualizar_produtos()


rod = tk.Frame(aba_prod)
rod.pack(fill="x", padx=8, pady=8)
botao(rod, "Novo produto", lambda: dialogo_produto()).pack(side="left", padx=2)
botao(rod, "Editar", editar_sel, "#3b6e52").pack(side="left", padx=2)
botao(rod, "Excluir", excluir_sel, VERMELHO).pack(side="left", padx=2)
tk.Label(rod, text="Estoque em vermelho = 5 ou menos").pack(side="right")
tp.bind("<Double-1>", editar_sel)
busca.trace_add("write", atualizar_produtos)

# ---------------- VENDAS ----------------
lbl_hoje = tk.Label(aba_vend, text="", font=("Segoe UI", 22, "bold"), fg=VERDE)
lbl_hoje.pack(anchor="w", padx=12, pady=(12, 0))
lbl_qtd = tk.Label(aba_vend, text="")
lbl_qtd.pack(anchor="w", padx=12)
vcols = ("data", "itens", "pag", "total")
tv = ttk.Treeview(aba_vend, columns=vcols, show="headings")
for c, t, w in zip(vcols, ("Data", "Itens", "Pagamento", "Total"), (200, 80, 140, 140)):
    tv.heading(c, text=t)
    tv.column(c, width=w, anchor="e" if c in ("itens", "total") else "w")
tv.pack(fill="both", expand=True, padx=8, pady=8)


def atualizar_vendas():
    hoje = datetime.now().strftime("%Y-%m-%d")
    soma, n = con.execute("SELECT COALESCE(SUM(total),0),COUNT(*) FROM vendas WHERE data LIKE ?",
                          (hoje + "%",)).fetchone()
    lbl_hoje.config(text="Hoje: " + r(soma))
    lbl_qtd.config(text=f"{n} venda(s) hoje")
    tv.delete(*tv.get_children())
    for vid, data, tot, pag in con.execute(
            "SELECT id,data,total,pagamento FROM vendas ORDER BY id DESC LIMIT 200"):
        q = con.execute("SELECT COALESCE(SUM(qtd),0) FROM itens WHERE venda_id=?", (vid,)).fetchone()[0]
        tv.insert("", "end", values=(data.replace("T", " "), q, pag, r(tot)))


def ao_trocar_aba(_):
    atualizar_produtos()
    atualizar_vendas()
    if abas.index(abas.select()) == 0:
        scan.focus_set()


abas.bind("<<NotebookTabChanged>>", ao_trocar_aba)
atualizar()
atualizar_produtos()
atualizar_vendas()
scan.focus_set()
root.mainloop()
