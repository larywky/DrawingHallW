import base64
import binascii
import os
import uuid
from functools import wraps
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector

app = Flask(__name__)

app.config.from_object("config")


def get_db_connection():
    return mysql.connector.connect(
        host=app.config["DB_HOST"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"],
        database=app.config["DB_NAME"],
        autocommit=True,
    )


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session and not session.get("is_admin"):
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


MOLDURAS = {"classica", "polaroid", "papel", "simples", "escura"}
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admhall123"


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Apenas o administrador pode apagar desenhos.", "danger")
            return redirect(url_for("galeria"))
        return view_func(*args, **kwargs)

    return wrapper


def buscar_desenhos(cursor, usuario_id=None):
    cursor.execute(
        """SELECT d.id, d.usuario_id, d.titulo, d.descricao, d.imagem,
                  d.moldura, d.data_publicacao, u.username, u.nome,
                  (SELECT COUNT(*) FROM curtidas c WHERE c.desenho_id = d.id) AS total_curtidas,
                  (SELECT COUNT(*) FROM curtidas c WHERE c.desenho_id = d.id AND c.usuario_id = %s) AS curtido
           FROM desenhos d JOIN usuarios u ON u.id = d.usuario_id
           WHERE (%s IS NULL OR d.usuario_id = %s)
           ORDER BY d.data_publicacao DESC""",
        (session.get("user_id"), usuario_id, usuario_id),
    )
    return cursor.fetchall()


def salvar_imagem(arquivo, desenho_canvas):
    if arquivo and arquivo.filename:
        nome_seguro = secure_filename(arquivo.filename)
        extensao = os.path.splitext(nome_seguro)[1].lower().lstrip(".")
        if extensao not in app.config["ALLOWED_EXTENSIONS"]:
            raise ValueError("Formato não permitido. Use PNG, JPG, JPEG ou GIF.")
        nome_arquivo = f"{uuid.uuid4().hex}.{extensao}"
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        arquivo.save(os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo))
        return f"uploads/{nome_arquivo}"

    if desenho_canvas:
        prefixo = "data:image/png;base64,"
        if not desenho_canvas.startswith(prefixo):
            raise ValueError("Não foi possível ler o desenho do canvas.")
        try:
            conteudo = base64.b64decode(desenho_canvas[len(prefixo):], validate=True)
        except (binascii.Error, ValueError) as erro:
            raise ValueError("O desenho enviado está inválido.") from erro
        if len(conteudo) > app.config["MAX_CONTENT_LENGTH"]:
            raise ValueError("O desenho excede o limite de 16 MB.")
        nome_arquivo = f"{uuid.uuid4().hex}.png"
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        with open(os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo), "wb") as imagem:
            imagem.write(conteudo)
        return f"uploads/{nome_arquivo}"

    raise ValueError("Faça um desenho no quadro ou selecione uma imagem.")


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("galeria"))
    return render_template("index.html")


@app.route("/galeria")
@login_required
def galeria():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    desenhos = buscar_desenhos(cursor)
    cursor.close()
    connection.close()
    return render_template("galeria.html", desenhos=desenhos)


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        username = request.form.get("username", "").strip()
        username_confirm = request.form.get("username_confirm", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not nome or not username or not username_confirm or not email or not senha:
            flash("Preencha todos os campos.", "danger")
            return render_template("cadastro.html")

        if username.casefold() != username_confirm.casefold():
            flash("Os nomes de usuário não conferem.", "danger")
            return render_template("cadastro.html")
        if username.casefold() == ADMIN_USERNAME:
            flash("Esse nome de usuário está reservado.", "danger")
            return render_template("cadastro.html")

        if len(senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "danger")
            return render_template("cadastro.html")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM usuarios WHERE username = %s OR email = %s",
            (username, email),
        )
        if cursor.fetchone():
            flash("Nome de usuário ou e-mail já cadastrados.", "danger")
            cursor.close()
            connection.close()
            return render_template("cadastro.html")

        senha_hash = generate_password_hash(senha)
        cursor.execute(
            "INSERT INTO usuarios (nome, username, email, senha) VALUES (%s, %s, %s, %s)",
            (nome, username, email, senha_hash),
        )
        session.clear()
        session["user_id"] = cursor.lastrowid
        session["username"] = username
        session["nome"] = nome
        cursor.close()
        connection.close()

        flash("Cadastro realizado com sucesso! Boas-vindas ao DrawingHall.", "success")
        return redirect(url_for("galeria"))

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_field = request.form.get("login", "").strip()
        senha = request.form.get("senha", "")

        if not login_field or not senha:
            flash("Informe o e-mail ou nome de usuário e a senha.", "danger")
            return render_template("login.html")

        if login_field.casefold() == ADMIN_USERNAME:
            if senha == ADMIN_PASSWORD:
                session.clear()
                session["is_admin"] = True
                session["username"] = ADMIN_USERNAME
                session["nome"] = "Administrador"
                flash("Login de administrador realizado.", "success")
                return redirect(url_for("galeria"))
            flash("Credenciais inválidas.", "danger")
            return render_template("login.html")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nome, username, senha FROM usuarios WHERE username = %s OR email = %s",
            (login_field, login_field),
        )
        usuario = cursor.fetchone()
        cursor.close()
        connection.close()

        if usuario and check_password_hash(usuario["senha"], senha):
            session.clear()
            session["user_id"] = usuario["id"]
            session["username"] = usuario["username"]
            session["nome"] = usuario["nome"]
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("galeria"))

        flash("Credenciais inválidas.", "danger")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("index"))


@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    if session.get("is_admin"):
        return redirect(url_for("galeria"))
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        moldura = request.form.get("moldura", "classica")
        arquivo = request.files.get("imagem")
        desenho_canvas = request.form.get("desenho_canvas", "")

        if not titulo:
            flash("Dê um título ao seu desenho.", "danger")
            return redirect(url_for("perfil"))
        if moldura not in MOLDURAS:
            flash("Escolha uma das molduras disponíveis.", "danger")
            return redirect(url_for("perfil"))
        if arquivo and arquivo.filename and desenho_canvas:
            flash("Escolha entre enviar uma imagem ou usar o desenho do quadro.", "danger")
            return redirect(url_for("perfil"))

        try:
            caminho_imagem = salvar_imagem(arquivo, desenho_canvas)
        except ValueError as erro:
            flash(str(erro), "danger")
            return redirect(url_for("perfil"))

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO desenhos (usuario_id, titulo, descricao, imagem, moldura) VALUES (%s, %s, %s, %s, %s)",
            (session["user_id"], titulo, descricao, caminho_imagem, moldura),
        )
        cursor.close()
        connection.close()
        flash("Desenho publicado na galeria!", "success")
        return redirect(url_for("perfil"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, nome, username, email, bio, foto FROM usuarios WHERE id = %s",
        (session["user_id"],),
    )
    usuario = cursor.fetchone()
    desenhos = buscar_desenhos(cursor, session["user_id"])
    cursor.close()
    connection.close()
    return render_template("perfil.html", usuario=usuario, desenhos=desenhos)


@app.route("/artista/<username>")
@login_required
def perfil_publico(username):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, nome, username, bio, foto FROM usuarios WHERE username = %s",
        (username,),
    )
    usuario = cursor.fetchone()
    if not usuario:
        cursor.close()
        connection.close()
        return "Artista não encontrado.", 404
    desenhos = buscar_desenhos(cursor, usuario["id"])
    cursor.close()
    connection.close()
    return render_template("perfil_publico.html", usuario=usuario, desenhos=desenhos)


@app.route("/curtir/<int:desenho_id>", methods=["POST"])
@login_required
def curtir(desenho_id):
    if session.get("is_admin"):
        flash("A conta de administrador não pode curtir desenhos.", "warning")
        return redirect(url_for("galeria"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT usuario_id FROM desenhos WHERE id = %s", (desenho_id,))
    desenho = cursor.fetchone()
    if not desenho or desenho["usuario_id"] == session["user_id"]:
        cursor.close()
        connection.close()
        flash("Você pode curtir apenas desenhos de outras pessoas.", "warning")
        return redirect(url_for("galeria"))
    cursor.execute(
        "SELECT id FROM curtidas WHERE usuario_id = %s AND desenho_id = %s",
        (session["user_id"], desenho_id),
    )
    curtida = cursor.fetchone()
    if curtida:
        cursor.execute("DELETE FROM curtidas WHERE id = %s", (curtida["id"],))
    else:
        cursor.execute(
            "INSERT INTO curtidas (usuario_id, desenho_id) VALUES (%s, %s)",
            (session["user_id"], desenho_id),
        )
    cursor.close()
    connection.close()

    destino = request.form.get("destino", "galeria")
    if destino == "perfil":
        return redirect(url_for("perfil"))
    if destino.startswith("artista:"):
        return redirect(url_for("perfil_publico", username=destino.split(":", 1)[1]))
    return redirect(url_for("galeria"))


@app.route("/desenho/<int:desenho_id>/apagar", methods=["POST"])
@admin_required
def apagar_desenho(desenho_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT imagem FROM desenhos WHERE id = %s", (desenho_id,))
    desenho = cursor.fetchone()
    if desenho:
        cursor.execute("DELETE FROM desenhos WHERE id = %s", (desenho_id,))
        pasta_uploads = os.path.abspath(app.config["UPLOAD_FOLDER"])
        caminho = os.path.abspath(os.path.join(pasta_uploads, os.path.basename(desenho["imagem"])))
        if os.path.dirname(caminho) == pasta_uploads and os.path.isfile(caminho):
            os.remove(caminho)
        flash("Desenho apagado da galeria.", "success")
    else:
        flash("Esse desenho não foi encontrado.", "warning")
    cursor.close()
    connection.close()
    return redirect(url_for("galeria"))


@app.route("/area-protegida")
@login_required
def area_protegida():
    return f"Olá, {session.get('nome')}! Esta área exige login."


@app.route("/db-test")
def db_test():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        resultado = cursor.fetchone()
        cursor.close()
        connection.close()
        return f"Conexão MySQL OK: {resultado}"
    except Exception as e:
        return f"Erro na conexão com MySQL: {e}", 500


if __name__ == "__main__":
    app.run(debug=True)
