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

# Ruta para la página de inicio (login)
@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('login.html')

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
        query = "SELECT contrasena, nombre FROM clientes WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()

        if result and check_password_hash(result[0], contrasena):
            session['email'] = email  # Guardar email en la sesión
            session['nombre_cliente'] = result[1]  # Guardar el nombre del cliente
            return redirect(url_for('registrar_pago'))  # Redirigir al formulario de registro de pago
        else:
            return jsonify({"error": "Correo o contraseña incorrectos"}), 400
    except Exception as ex:
        print("Error al iniciar sesión:", ex)
        return jsonify({"error": str(ex)}), 500
    finally:
        connection.close()

# Ruta para registrar pagos
@app.route('/registrar-pago', methods=['GET', 'POST'])
def registrar_pago():
    if 'email' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Extraer datos del formulario
        fecha_inicial = request.form['fecha_inicial']
        fecha_final = request.form['fecha_final']
        cantidad_pago = request.form['cantidad_pago']
        frecuencia = request.form['frecuencia']
        fecha_cobro = request.form['fecha_cobro']
        estado_pago = "Pendiente"  # Estado por defecto

        connection = get_db_connection()
        if connection is None:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        try:
            cursor = connection.cursor()
            
            # Obtener el cliente_id usando el email del usuario en sesión
            query_cliente_id = "SELECT cliente_id FROM clientes WHERE email = %s"
            cursor.execute(query_cliente_id, (session['email'],))
            cliente_id_result = cursor.fetchone()

            if cliente_id_result is None:
                return jsonify({"error": "No se encontró el cliente con ese email"}), 404

            cliente_id = cliente_id_result[0]

            # Insertar el pago en la tabla 'pagos'
            query_insert_pago = """
            INSERT INTO pagos (cliente_id, cantidad_pago, frecuencia, fecha_inicial, fecha_final, fecha_cobro, estado_pago)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING pago_id
            """
            cursor.execute(query_insert_pago, (cliente_id, cantidad_pago, frecuencia, fecha_inicial, fecha_final, fecha_cobro, estado_pago))
            pago_id = cursor.fetchone()[0]  # Capturar el pago_id generado
            connection.commit()

            return redirect(url_for('dashboard'))  # Redirigir al dashboard tras registrar el pago

        except Exception as ex:
            print("Error al registrar el pago:", ex)
            return jsonify({"error": str(ex)}), 500
        finally:
            connection.close()

    # Mostrar formulario de registro de pago
    return render_template('registrar_pago.html', nombre_cliente=session.get('nombre_cliente', 'Usuario'))

# Ruta del dashboard
@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('home'))
    return f"Bienvenido, {session['nombre_cliente']}! Este es tu dashboard."

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Validar el email
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
