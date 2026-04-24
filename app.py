from flask import Flask, render_template, request, redirect
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def conectar():
    return psycopg2.connect(DATABASE_URL)

# =========================
# INIT BANCO
# =========================
def init_db():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id SERIAL PRIMARY KEY,
        nome TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS garcons (
        id SERIAL PRIMARY KEY,
        nome TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS estoque (
        id SERIAL PRIMARY KEY,
        produto TEXT,
        local TEXT,
        quantidade INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS vendas (
        id SERIAL PRIMARY KEY,
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

    c.execute("SELECT nome FROM produtos")
    produtos = c.fetchall()

    c.execute("SELECT nome FROM garcons")
    garcons = c.fetchall()

    c.execute("""
        SELECT produto, local, SUM(quantidade)
        FROM estoque
        GROUP BY produto, local
    """)
    estoque = c.fetchall()

    c.execute("SELECT * FROM vendas ORDER BY id DESC")
    vendas = c.fetchall()

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
        c.execute("INSERT INTO produtos (nome) VALUES (%s)", (nome,))
    except:
        pass

    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/del_produto", methods=["POST"])
def del_produto():
    nome = request.form["nome"]

    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM produtos WHERE nome = %s", (nome,))

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
        c.execute("INSERT INTO garcons (nome) VALUES (%s)", (nome,))
    except:
        pass

    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/del_garcom", methods=["POST"])
def del_garcom():
    nome = request.form["nome"]

    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM garcons WHERE nome = %s", (nome,))

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
    c.execute("""
        INSERT INTO estoque (produto, local, quantidade)
        VALUES (%s, %s, %s)
    """, (produto, local, -qtd))

    # registra venda
    c.execute("""
        INSERT INTO vendas (garcom, produto, local, quantidade, data)
        VALUES (%s, %s, %s, %s, %s)
    """, (garcom, produto, local, qtd,
          datetime.now().strftime("%d/%m %H:%M")))

    conn.commit()
    conn.close()

    return redirect("/")

# =========================
# CANCELAR VENDA
# =========================
@app.route("/cancelar", methods=["POST"])
def cancelar():
    id_venda = request.form["id"]

    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT * FROM vendas WHERE id = %s", (id_venda,))
    venda = c.fetchone()

    if venda:
        produto = venda[2]
        local = venda[3]
        qtd = venda[4]

        # devolve estoque
        c.execute("""
            INSERT INTO estoque (produto, local, quantidade)
            VALUES (%s, %s, %s)
        """, (produto, local, qtd))

        c.execute("DELETE FROM vendas WHERE id = %s", (id_venda,))

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

    # tira do depósito
    c.execute("""
        INSERT INTO estoque (produto, local, quantidade)
        VALUES (%s, 'DEPOSITO', %s)
    """, (produto, -qtd))

    # adiciona no bar
    c.execute("""
        INSERT INTO estoque (produto, local, quantidade)
        VALUES (%s, %s, %s)
    """, (produto, local, qtd))

    conn.commit()
    conn.close()

    return redirect("/")

# =========================
if __name__ == "__main__":
    init_db()
    app.run()