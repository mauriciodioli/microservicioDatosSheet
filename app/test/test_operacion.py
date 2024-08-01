import pytest
from app import app, db
from models.usuario import Usuario
from models.operacion import Operacion

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_alta_operacion(client):
    # Primero, crear un usuario para la operación
    client.post('/usuarios/alta', json={
        'nombre': 'Test User',
        'email': 'test@example.com'
    })
    usuario = Usuario.query.first()

    response = client.post('/operaciones/alta', json={
        'tipo': 'Test Operacion',
        'monto': 100.0,
        'usuario_id': usuario.id
    })
    assert response.status_code == 200
    assert response.json['message'] == 'Operación creada correctamente'
