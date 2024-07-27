import pytest
from app import app, db
from models.usuario import Usuario

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

def test_alta_usuario(client):
    response = client.post('/usuarios/alta', json={
        'nombre': 'Test User',
        'email': 'test@example.com'
    })
    assert response.status_code == 200
    assert response.json['message'] == 'Usuario creado correctamente'
