from flask import Blueprint, render_template,current_app
import traceback
from app.models.usuario import Usuario
from app.models.workflows import Workflows
from sqlalchemy import text

views_controller = Blueprint('views_controller', __name__)

# Usar import dentro de las rutas para evitar el circular import
@views_controller.route('/')
def index():
    try:
        from app import db  # Importar aquí dentro de la función
        return render_template('index.html')
    except Exception as e:
        error_message = f"Error en index: {str(e)}"
        print(error_message)
        traceback.print_exc()
        return f"Error en index: {str(e)}", 500

@views_controller.route('/check_db') 
def check_db():
    try:
        from app import db  # Importar aquí dentro de la función
       
        app = current_app._get_current_object() 
        result = db.session.execute(text('SELECT 1'))
        with app.app_context():
            db.create_all()
            print("Tablas creadas correctamente")
        if result.scalar() == 1:
            usuario = db.session.query(Usuario).filter_by(id=1).first() 
            if usuario:
                print(f"ID: {usuario.id}")
                print(f"Nombre: {usuario.correo_electronico}")
                print(f"Correo electrónico: {usuario.roll}")
                new_workflow = Workflows(
                    nombre='nombre',
                    activado=1,
                    configuraciones='configuraciones',
                    user_id=1
                )
                db.session.add(new_workflow)
                db.session.commit()
            else:
                print("Usuario no encontrado")
            return 'Conexión a la base de datos exitosa!'
        else:
            return 'No se pudo establecer conexión a la base de datos.'
    except Exception as e:
        return f'Error en la conexión a la base de datos: {str(e)}'

@views_controller.route('/workflow/')
def workflow():
    try:
        print('test')
        return render_template('workflowUsuario.html')
    except Exception as e:
        return f'Error en la conexión a la base de datos: {str(e)}'
