from flask import Flask, request, jsonify
from functools import wraps
import jwt
import redis
import os

app = Flask(__name__)

# Configuración
API_KEY = "2f5ae96c-b558-4c7b-a590-a501ae1c3f6c"
JWT_SECRET = "your_jwt_secret_here"

# Configuración Redis para tracking de JWT
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-service')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def require_apikey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('X-Parse-REST-API-Key') == API_KEY:
            return view_function(*args, **kwargs)
        else:
            return jsonify({"error": "Invalid API Key"}), 401
    return decorated_function

def verify_jwt(token):
    try:
        # Verificar si el token ya fue usado
        if redis_client.get(f"used_token:{token}"):
            return False, "Token already used"
        
        # Decodificar y verificar el token
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        # Marcar el token como usado
        redis_client.setex(f"used_token:{token}", 
                         int(payload.get('timeToLifeSec', 3600)), 
                         'used')
        
        return True, None
    except jwt.ExpiredSignatureError:
        return False, "Token expired"
    except jwt.InvalidTokenError:
        return False, "Invalid token"
    except Exception as e:
        return False, str(e)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/DevOps', methods=['POST'])
@require_apikey
def devops():
    jwt_token = request.headers.get('X-JWT-KWY')
    if not jwt_token:
        return jsonify({"error": "Missing JWT"}), 401

    # Verificar JWT y su uso único
    is_valid, error_message = verify_jwt(jwt_token)
    if not is_valid:
        return jsonify({"error": f"Invalid JWT: {error_message}"}), 401

    data = request.json
    if not all(key in data for key in ["message", "to", "from", "timeToLifeSec"]):
        return jsonify({"error": "Missing required fields"}), 400

    response = {
        "message": f"Hello {data['to']} your message will be send"
    }
    return jsonify(response)

@app.route('/<path:path>', methods=['GET', 'PUT', 'DELETE', 'PATCH'])
def catch_all(path):
    # Permite las peticiones GET para la validación de Let's Encrypt
    if request.method == 'GET' and path.startswith('.well-known/acme-challenge/'):
        return '', 404  # Deja que cert-manager maneje esta ruta
    return "ERROR", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)