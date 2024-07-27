#!/bin/bash

# Modify _app.py in websocket library
pip uninstall -y websocket-client
pip install websocket-client==0.57.0
sed -i 's/isAlive/is_alive/g' /usr/local/lib/python3.12/site-packages/websocket/_app.py

# Modify service.py in pyRofex library
echo 'def _add_environment_config(enumCuenta, env):' >> /usr/local/lib/python3.12/site-packages/pyRofex/service.py
echo '    enum = enumCuenta' >> /usr/local/lib/python3.12/site-packages/pyRofex/service.py
echo '    setattr(Environment, enumCuenta, enum)' >> /usr/local/lib/python3.12/site-packages/pyRofex/service.py
echo '    globals.environment_config[enumCuenta] = env' >> /usr/local/lib/python3.12/site-packages/pyRofex/service.py
sed -i '/^def _validate_environment(environment):$/,/^ *raise ApiException(\"Invalid Environment.\")/ s/^ *if not isinstance(environment, Environment):/#&/' /usr/local/lib/python3.12/site-packages/pyRofex/service.py

# Add line to position 39 in __init__.py of pyRofex library
sed -i '39i\from .service import _add_environment_config' /usr/local/lib/python3.12/site-packages/pyRofex/__init__.py

# Add Environment class to enums.py of pyRofex library
sed -i '9i\class Environment:' /usr/local/lib/python3.12/site-packages/pyRofex/components/enums.py
sed -i '10i\    REMARKET = 1' /usr/local/lib/python3.12/site-packages/pyRofex/components/enums.py
sed -i '11i\    LIVE = 2' /usr/local/lib/python3.12/site-packages/pyRofex/components/enums.py
