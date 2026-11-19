
from flask import Flask, render_template, request, redirect, url_for, flash
from banco import conectar, criar_banco
from datetime import date

app = Flask(__name__)
app.secret_key = "chocotech_chave_local"

# Entidades e campos permitidos
MODULOS = {
    "produtos": {
        "titulo": "Produtos",
        "campos": ["nome", "tipo", "preco", "quantidade"],
        "labels": ["Nome", "Tipo", "Preço", "Quantidade"]
    },
    "ingredientes": {
        "titulo": "Ingredientes",
        "campos": ["nome", "unidade", "quantidade"],
        "labels": ["Nome", "Unidade", "Quantidade"]
    },
    "funcionarios": {
        "titulo": "Funcionários",
        "campos": ["nome", "cargo", "telefone"],
        "labels": ["Nome", "Cargo", "Telefone"]
    },
    "clientes": {
        "titulo": "Clientes",
        "campos": ["nome", "telefone", "email"],
        "labels": ["Nome", "Telefone", "E-mail"]
    }
}

@app.route("/")
def inicio():
    conexao = conectar()
    cursor = conexao.cursor()

    dados = {}

    for tabela in MODULOS:
        cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
        dados[tabela] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM producao")
    dados["producao"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM vendas")
    dados["vendas"] = cursor.fetchone()[0]

    conexao.close()

    return render_template("index.html", dados=dados)


@app.route("/<modulo>")
def listar(modulo):
    if modulo not in MODULOS:
        return "Módulo não encontrado", 404

    conexao = conectar()
    cursor = conexao.cursor()

    campos = MODULOS[modulo]["campos"]
    colunas = ", ".join(campos)

    cursor.execute(f"SELECT id, {colunas} FROM {modulo}")
    registros = cursor.fetchall()

    conexao.close()

    return render_template(
        "listar.html",
        modulo=modulo,
        titulo=MODULOS[modulo]["titulo"],
        campos=campos,
        labels=MODULOS[modulo]["labels"],
        registros=registros
    )


@app.route("/novo/<modulo>", methods=["GET", "POST"])
def novo(modulo):
    if modulo not in MODULOS:
        return "Módulo não encontrado", 404

    config = MODULOS[modulo]

    if request.method == "POST":
        valores = [request.form.get(campo, "").strip()
                   for campo in config["campos"]]

        if not all(valores):
            flash("Preencha todos os campos obrigatórios.")
            return redirect(url_for("novo", modulo=modulo))

        try:
            if modulo == "produtos":
                valores[2] = float(valores[2].replace(",", "."))
                valores[3] = int(valores[3])

            elif modulo == "ingredientes":
                valores[2] = float(valores[2].replace(",", "."))

            colunas = ", ".join(config["campos"])
            marcadores = ", ".join(["?"] * len(valores))

            conexao = conectar()
            conexao.execute(
                f"INSERT INTO {modulo} ({colunas}) VALUES ({marcadores})",
                valores
            )
            conexao.commit()
            conexao.close()

            flash("Cadastro realizado com sucesso!")
            return redirect(url_for("listar", modulo=modulo))

        except (ValueError, TypeError):
            flash("Informe valores numéricos válidos.")
            return redirect(url_for("novo", modulo=modulo))

    return render_template(
        "formulario.html",
        titulo="Cadastrar " + config["titulo"],
        modulo=modulo,
        campos=config["campos"],
        labels=config["labels"],
        registro=None
    )


@app.route("/editar/<modulo>/<int:id>", methods=["GET", "POST"])
def editar(modulo, id):
    if modulo not in MODULOS:
        return "Módulo não encontrado", 404

    config = MODULOS[modulo]
    conexao = conectar()
    cursor = conexao.cursor()

    if request.method == "POST":
        valores = [request.form.get(campo, "").strip()
                   for campo in config["campos"]]

        if not all(valores):
            conexao.close()
            flash("Preencha todos os campos.")
            return redirect(url_for("editar", modulo=modulo, id=id))

        try:
            if modulo == "produtos":
                valores[2] = float(valores[2].replace(",", "."))
                valores[3] = int(valores[3])
            elif modulo == "ingredientes":
                valores[2] = float(valores[2].replace(",", "."))

            atribuicoes = ", ".join(
                campo + " = ?" for campo in config["campos"]
            )

            cursor.execute(
                f"UPDATE {modulo} SET {atribuicoes} WHERE id = ?",
                valores + [id]
            )

            conexao.commit()
            conexao.close()

            flash("Registro atualizado!")
            return redirect(url_for("listar", modulo=modulo))

        except ValueError:
            conexao.close()
            flash("Informe valores numéricos válidos.")
            return redirect(url_for("editar", modulo=modulo, id=id))

    cursor.execute(
        f"SELECT id, {', '.join(config['campos'])} FROM {modulo} WHERE id = ?",
        (id,)
    )
    registro = cursor.fetchone()
    conexao.close()

    if not registro:
        return "Registro não encontrado", 404

    return render_template(
        "formulario.html",
        titulo="Editar " + config["titulo"],
        modulo=modulo,
        campos=config["campos"],
        labels=config["labels"],
        registro=registro
    )


@app.route("/excluir/<modulo>/<int:id>", methods=["POST"])
def excluir(modulo, id):
    if modulo not in MODULOS:
        return "Módulo não encontrado", 404

    conexao = conectar()
    conexao.execute(
        f"DELETE FROM {modulo} WHERE id = ?",
        (id,)
    )
    conexao.commit()
    conexao.close()

    flash("Registro excluído!")
    return redirect(url_for("listar", modulo=modulo))


@app.route("/producao", methods=["GET", "POST"])
def producao():
    conexao = conectar()

    if request.method == "POST":
        try:
            produto_id = int(request.form["produto_id"])
            quantidade = int(request.form["quantidade"])

            if quantidade <= 0:
                raise ValueError

            cursor = conexao.cursor()
            cursor.execute(
                "SELECT id FROM produtos WHERE id = ?",
                (produto_id,)
            )

            if not cursor.fetchone():
                raise ValueError

            cursor.execute("""
                INSERT INTO producao (produto_id, quantidade, data)
                VALUES (?, ?, ?)
            """, (produto_id, quantidade, date.today().isoformat()))

            cursor.execute("""
                UPDATE produtos
                SET quantidade = quantidade + ?
                WHERE id = ?
            """, (quantidade, produto_id))

            conexao.commit()
            flash("Produção registrada com sucesso!")

        except (ValueError, KeyError):
            conexao.rollback()
            flash("Dados de produção inválidos.")

        finally:
            conexao.close()

        return redirect(url_for("producao"))

    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome FROM produtos")
    produtos = cursor.fetchall()

    cursor.execute("""
        SELECT producao.id, produtos.nome,
               producao.quantidade, producao.data
        FROM producao
        JOIN produtos ON produtos.id = producao.produto_id
        ORDER BY producao.id DESC
    """)
    registros = cursor.fetchall()

    conexao.close()

    return render_template(
        "producao.html",
        produtos=produtos,
        registros=registros
    )


if __name__ == "__main__":
    criar_banco()

    print("ChocoTech iniciado!")
    print("Acesse: http://127.0.0.1:5000")

    app.run(debug=True)
