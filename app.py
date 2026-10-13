import csv
import io
from flask import Flask, render_template, request, redirect, url_for, Response, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-secreta-super-segura'  # Necesaria para Flask-Login
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'error'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- MODELOS DE BASE DE DATOS ---
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nif = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    descuento = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()
    
    # Crear un usuario administrador por defecto si no existe ninguno
    if not Usuario.query.first():
        hashed_password = generate_password_hash('PasswordSegura123', method='pbkdf2:sha256')
        admin = Usuario(email='admin@gmail.com', password=hashed_password)
        db.session.add(admin)
        db.session.commit()

# --- RUTAS DE AUTENTICACIÓN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.password, password):
            login_user(usuario)
            return redirect(url_for('home'))
        else:
            flash('Credenciales incorrectas. Revisa tu email y contraseña.', 'error')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- RUTAS CRUD (Protegidas) ---
@app.route('/')
@login_required
def home():
    lista_clientes = Cliente.query.all()
    return render_template('index.html', clientes=lista_clientes)

@app.route('/agregar', methods=['POST'])
@login_required
def agregar_cliente():
    nif = request.form['nif']
    nombre = request.form['nombre']
    email = request.form['email']
    telefono = request.form['telefono']
    descuento = float(request.form['descuento'])
    
    nuevo_cliente = Cliente(nif=nif, nombre=nombre, email=email, telefono=telefono, descuento=descuento)
    db.session.add(nuevo_cliente)
    db.session.commit()
    
    return redirect(url_for('home'))

@app.route('/eliminar/<int:id>')
@login_required
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        cliente.nif = request.form['nif']
        cliente.nombre = request.form['nombre']
        cliente.email = request.form['email']
        cliente.telefono = request.form['telefono']
        cliente.descuento = float(request.form['descuento'])
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('editar.html', cliente=cliente)

@app.route('/exportar')
@login_required
def exportar_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escribir la cabecera
    writer.writerow(['NIF', 'Nombre', 'Email', 'Telefono', 'Descuento'])
    
    # Obtener todos los clientes de la base de datos
    clientes = Cliente.query.all()
    
    # Escribir cada cliente en una fila
    for c in clientes:
        writer.writerow([c.nif, c.nombre, c.email, c.telefono, f"{c.descuento}%"])
    
    # Preparar la respuesta para descargar
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=clientes.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)