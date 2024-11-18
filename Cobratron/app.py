from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import pg8000
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = 'secret_key'  # Cambia esta clave por algo seguro

# Configuración de la base de datos
DATABASE_CONFIG = {
    'database': 'cobratron',
    'user': 'postgres',
    'password': 'adi2012',
    'host': 'localhost',
    'port': 5432
}

# Función para obtener la conexión a la base de datos
def get_db_connection():
    try:
        connection = pg8000.connect(**DATABASE_CONFIG)
        return connection
    except Exception as ex:
        print("Error al conectar a la base de datos:", ex)
        return None

# Ruta para la página de inicio (login o registro)
@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('login.html')  # Renderiza el formulario de login

# Ruta para el inicio de sesión
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    contrasena = request.form['contrasena']

    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor()
        query = """
        SELECT contrasena FROM Clientes WHERE email = %s
        """
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        
        if result and check_password_hash(result[0], contrasena):
            session['email'] = email  # Guardar email del usuario en la sesión
            return redirect(url_for('dashboard'))  # Redirige al dashboard o página protegida
        else:
            return jsonify({"error": "Correo o contraseña incorrectos"}), 400
    except Exception as ex:
        print("Error al iniciar sesión:", ex)
        return jsonify({"error": str(ex)}), 500
    finally:
        connection.close()

# Ruta de dashboard (solo accesible si el usuario está logueado)
@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('home'))  # Si no está logueado, redirige al login

    return f'Bienvenido, {session["email"]}! Este es tu dashboard.'

# Validar el email
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

# Ruta de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form.get('telefono')
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']

        # Validación de las contraseñas
        if contrasena != confirmar_contrasena:
            return jsonify({"error": "Las contraseñas no coinciden"}), 400

        # Validar el email
        if not is_valid_email(email):
            return jsonify({"error": "El formato del email es inválido"}), 400

        # Hashear la contraseña
        contrasena_hashed = generate_password_hash(contrasena)

        connection = get_db_connection()
        if connection is None:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        try:
            cursor = connection.cursor()
            query = """
            INSERT INTO Clientes (nombre, email, telefono, contrasena)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (nombre, email, telefono, contrasena_hashed))
            connection.commit()
            cursor.close()
            return redirect(url_for('home'))  # Después de registrarse, redirige al login
        except Exception as ex:
            print("Error al registrar usuario:", ex)
            return jsonify({"error": str(ex)}), 500
        finally:
            connection.close()

    return render_template('register.html')  # Muestra el formulario de registro

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
