import mysql.connector
from functools import wraps
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

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
        if "user_id" not in session:
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


@app.route("/")
def index():
    desenhos = [
        {
            "titulo": "Madrugada em Tons Pastel",
            "autor": "Ana",
            "imagem": "https://images.unsplash.com/photo-1515405295579-ba7b45403062?auto=format&fit=crop&w=900&q=80",
            "moldura": "Polaroid",
            "descricao": "Estudo de luz e cor em um cenário tranquilo.",
        },
        {
            "titulo": "Pássaro de Papel",
            "autor": "Pedro",
            "imagem": "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?auto=format&fit=crop&w=900&q=80",
            "moldura": "Clássica",
            "descricao": "A ideia nasceu de uma folha em branco e um traço leve.",
        },
        {
            "titulo": "Jardim Silencioso",
            "autor": "Beatriz",
            "imagem": "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?auto=format&fit=crop&w=900&q=80",
            "moldura": "Papel",
            "descricao": "Uma composição pequena inspirada em paisagens íntimas.",
        },
    ]
    return render_template("index.html", desenhos=desenhos)


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not nome or not username or not email or not senha:
            flash("Preencha todos os campos.", "danger")
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
        connection.commit()
        cursor.close()
        connection.close()

        flash("Cadastro realizado com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_field = request.form.get("login", "").strip()
        senha = request.form.get("senha", "")

        if not login_field or not senha:
            flash("Informe o e-mail ou nome de usuário e a senha.", "danger")
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
            return redirect(url_for("index"))

        flash("Credenciais inválidas.", "danger")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("index"))


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
