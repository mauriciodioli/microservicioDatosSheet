def validate_operacion(data):
    if 'tipo' not in data or 'monto' not in data or 'usuario_id' not in data:
        return False
    return True
