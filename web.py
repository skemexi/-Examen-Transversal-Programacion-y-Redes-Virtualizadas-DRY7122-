from flask import Flask, request, render_template_string
import sqlite3
import hashlib

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            hash_password TEXT
        )
    ''')
    conn.commit()
    conn.close()


def insertar_usuario(nombre, password):
    hash_pass = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn = sqlite3.connect('usuarios.db')
        c = conn.cursor()
        c.execute('INSERT INTO usuarios (nombre, hash_password) VALUES (?, ?)', (nombre, hash_pass))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # usuario ya existe
    finally:
        conn.close()

def validar_usuario(nombre, password):
    hash_pass = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('SELECT * FROM usuarios WHERE nombre=? AND hash_password=?', (nombre, hash_pass))
    result = c.fetchone()
    conn.close()
    return result is not None


login_form = '''
<!doctype html>
<title>Login Grupo</title>
<h2>Login Integrantes</h2>
<form method=post>
    Nombre: <input type=text name=nombre><br>
    Clave: <input type=password name=password><br>
    <input type=submit value=Login>
</form>
<p>{{ mensaje }}</p>
'''


@app.route('/', methods=['GET', 'POST'])
def login():
    mensaje = ''
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['password']
        if validar_usuario(nombre, password):
            mensaje = f'¡Bienvenido {nombre}!'
        else:
            mensaje = 'Usuario o contraseña incorrectos.'
    return render_template_string(login_form, mensaje=mensaje)

if __name__ == "__main__":
    init_db()
    # Insertar usuarios del examen
    insertar_usuario("pedro coronado", "clave1")
    insertar_usuario("pablo nova", "clave2")
    app.run(host='0.0.0.0', port=5800)
