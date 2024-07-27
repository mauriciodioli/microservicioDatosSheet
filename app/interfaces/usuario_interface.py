def validate_usuario(data):
    if 'nombre' not in data or 'email' not in data:
        return False
    return True
