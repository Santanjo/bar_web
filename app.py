from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

def conectar():
    return sqlite3.connect("banco.db")

# =========================
# INIT BANCO
# =========================
def init_db():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS garcons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto TEXT,
        local TEXT,
        quantidade INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        garcom TEXT,
        produto TEXT,
        local TEXT,
        quantidade INTEGER,
        data TEXT
    )
    """)

    conn.commit()
    conn.close()

# =========================
# HOME
# =========================
@app.route("/")
def index():
    conn = conectar()
    c = conn.cursor()

    produtos = c.execute("SELECT nome FROM produtos").fetchall()
    garcons = c.execute("SELECT nome FROM garcons").fetchall()
    estoque = c.execute("SELECT produto, local, SUM(quantidade) FROM estoque GROUP BY produto, local").fetchall()
    vendas = c.execute("SELECT * FROM vendas ORDER BY id DESC").fetchall()

    conn.close()

    return render_template("index.html",
                           produtos=produtos,
                           garcons=garcons,
                           estoque=estoque,
                           vendas=vendas)

# =========================
# PRODUTO
# =========================
@app.route("/add_produto", methods=["POST"])
def add_produto():
    nome = request.form["nome"]

    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO produtos (nome) VALUES (?)", (nome,))
    except:
        pass
    conn.commit()
    conn.close()

    return redirect("/")

# =========================
# GARÇOM
# =========================
@app.route("/add_garcom", methods=["POST"])
def add_garcom():
    nome = request.form["nome"]

    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO garcons (nome) VALUES (?)", (nome,))
    except:
        pass
    conn.commit()
    conn.close()

    return redirect("/")

# =========================
# VENDA
# =========================
@app.route("/vender", methods=["POST"])
def vender():
    produto = request.form["produto"]
    garcom = request.form["garcom"]
    local = request.form["local"]
    qtd = int(request.form["qtd"])

    conn = conectar()
    c = conn.cursor()

    # baixa estoque
    c.execute("INSERT INTO estoque (produto, local, quantidade) VALUES (?, ?, ?)",
              (produto, local, -qtd))

    # registra venda
    c.execute("INSERT INTO vendas (garcom, produto, local, quantidade, data) VALUES (?, ?, ?, ?, ?)",
              (garcom, produto, local, qtd, datetime.now().strftime("%d/%m %H:%M")))

    conn.commit()
    conn.close()

    return redirect("/")

# =========================
# REPOSIÇÃO
# =========================
@app.route("/reposicao", methods=["POST"])
def reposicao():
    produto = request.form["produto"]
    local = request.form["local"]
    qtd = int(request.form["qtd"])

    conn = conectar()
    c = conn.cursor()

    # tira do deposito
    c.execute("INSERT INTO estoque VALUES (NULL, ?, 'DEPOSITO', ?)", (produto, -qtd))

    # adiciona no bar
    c.execute("INSERT INTO estoque VALUES (NULL, ?, ?, ?)", (produto, local, qtd))

    conn.commit()
    conn.close()

    return redirect("/")

# =========================
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)