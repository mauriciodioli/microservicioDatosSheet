from flask import Blueprint, render_template, session,request, redirect, url_for, flash,jsonify
from flask_marshmallow import Marshmallow
from app.utils.common import db
from sqlalchemy import inspect

ma = Marshmallow()

cuentas = Blueprint('cuentas',__name__) 



class Cuenta(db.Model):
    __tablename__ = 'cuentas'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False) 
    userCuenta = db.Column(db.String(120), unique=True, nullable=False)
    passwordCuenta = db.Column(db.LargeBinary(128), nullable=False)
    accountCuenta = db.Column(db.String(500), nullable=True)
    selector = db.Column(db.String(500), nullable=True)
  

    
 # constructor
    def __init__(self, id,user_id,userCuenta,passwordCuenta,accountCuenta,selector):
        self.id = id
        self.user_id = user_id
        self.userCuenta = userCuenta
        self.passwordCuenta = passwordCuenta
        self.accountCuenta = accountCuenta
        self.selector = selector

   
    def __repr__(self):
        return f"Cuenta(id={self.id}, user_id={self.user_id}, userCuenta={self.userCuenta}, passwordCuenta={self.passwordCuenta}, accountCuenta={self.accountCuenta}, selector={self.selector})"
    @classmethod
    def crear_tabla_cuentas(self):
         insp = inspect(db.engine)
         if not insp.has_table("cuentas"):
              db.create_all()
             
    
        
class MerShema(ma.Schema):
    class Meta:
        fields = ("id", "user_id" ,"userCuenta","passwordCuenta","accountCuenta","selector")

mer_schema = MerShema()
mer_shema = MerShema(many=True)

