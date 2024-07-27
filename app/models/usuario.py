from flask_marshmallow import Marshmallow
from flask import Blueprint
from app.utils.common import db
from sqlalchemy import inspect
from sqlalchemy.orm import relationship


ma = Marshmallow()

usuario = Blueprint('usuario',__name__) 



class Usuario(db.Model):
    __tablename__ = 'usuarios'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activo = db.Column(db.Boolean, nullable=False, default=False)    
    correo_electronico = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.LargeBinary(128), nullable=False)
    token = db.Column(db.String(1000), nullable=True)
    roll = db.Column(db.String(20), nullable=False, default='regular')
    refresh_token = db.Column(db.String(1000), nullable=True)
 
   
 # constructor
    def __init__(self, id,correo_electronico,token,refresh_token,activo,password,roll='USUARIO'):
        self.id = id
        self.correo_electronico = correo_electronico
        self.token = token
        self.refresh_token = refresh_token
        self.activo = activo        
        self.password = password
        self.roll = roll

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.activo

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    @classmethod
    def crear_tabla_usuarios(serlf):
         insp = inspect(db.engine)
         if not insp.has_table("usuarios"):
              db.create_all()
    
        
class MerShema(ma.Schema):
    class Meta:
        fields = ("id",  "correo_electronico","token","refresh_token","activo","password","roll")

mer_schema = MerShema()
mer_shema = MerShema(many=True)