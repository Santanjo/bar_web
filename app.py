from flask import Flask, render_template, request, redirect
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def conectar():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id SERIAL PRIMARY KEY,
        nome TEXT UNIQUE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS garcons (
        id SERIAL PRIMARY KEY,
        nome TEXT UNIQUE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS estoque (
        produto TEXT,
        local TEXT,
        quantidade INTEGER,
        PRIMARY KEY (produto, local)
    )
    """)

    cur.execute("""
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
    cur.close()
    conn.close()

# HOME
@app.route("/")
def index():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT nome FROM produtos")
    produtos = [p[0] for p in cur.fetchall()]

    cur.execute("SELECT nome FROM garcons")
    garcons = [g[0] for g in cur.fetchall()]

    cur.execute("SELECT * FROM vendas ORDER BY id DESC")
    vendas = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("index.html", produtos=produtos, garcons=garcons, vendas=vendas)

# PRODUTO
@app.route("/add_produto", methods=["POST"])
def add_produto():
    nome = request.form["nome"]

    conn = conectar()
    cur = conn.cursor()

    cur.execute("INSERT INTO produtos (nome) VALUES (%s) ON CONFLICT DO NOTHING", (nome,))

    conn.commit()
    conn.close()

    return redirect("/")

# GARÇOM
@app.route("/add_garcom", methods=["POST"])
def add_garcom():
    nome = request.form["nome"]

    conn = conectar()
    cur = conn.cursor()

    cur.execute("INSERT INTO garcons (nome) VALUES (%s) ON CONFLICT DO NOTHING", (nome,))

    conn.commit()
    conn.close()

    return redirect("/")

# ESTOQUE
def get_estoque(produto, local):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT quantidade FROM estoque WHERE produto=%s AND local=%s", (produto, local))
    res = cur.fetchone()

    conn.close()
    return res[0] if res else 0

def atualizar_estoque(produto, local, qtd):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO estoque (produto, local, quantidade)
    VALUES (%s, %s, %s)
    ON CONFLICT (produto, local)
    DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade
    """, (produto, local, qtd))

    conn.commit()
    conn.close()

# VENDA
@app.route("/vender", methods=["POST"])
def vender():
    produto = request.form["produto"]
    garcom = request.form["garcom"]
    local = request.form["local"]
    qtd = int(request.form["qtd"])

    if get_estoque(produto, local) < qtd:
        return "Sem estoque"

    atualizar_estoque(produto, local, -qtd)

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO vendas (garcom, produto, local, quantidade, data)
    VALUES (%s, %s, %s, %s, %s)
    """, (garcom, produto, local, qtd, datetime.now().strftime("%d/%m %H:%M")))

    conn.commit()
    conn.close()

    return redirect("/")

# CANCELAR
@app.route("/cancelar/<int:id>")
def cancelar(id):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT produto, local, quantidade FROM vendas WHERE id=%s", (id,))
    venda = cur.fetchone()

    if venda:
        atualizar_estoque(venda[0], venda[1], venda[2])
        cur.execute("DELETE FROM vendas WHERE id=%s", (id,))

    conn.commit()
    conn.close()

    return redirect("/")

# REPOSIÇÃO
@app.route("/reposicao", methods=["POST"])
def reposicao():
    produto = request.form["produto"]
    destino = request.form["local"]
    qtd = int(request.form["qtd"])

    if get_estoque(produto, "DEPOSITO") < qtd:
        return "Sem estoque no depósito"

    atualizar_estoque(produto, "DEPOSITO", -qtd)
    atualizar_estoque(produto, destino, qtd)

    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run()