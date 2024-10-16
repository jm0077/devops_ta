from flask import Flask, request, jsonify
from functools import wraps
import jwt
import datetime

app = Flask(__name__)

API_KEY = "2f5ae96c-b558-4c7b-a590-a501ae1c3f6c"
JWT_SECRET = "your_jwt_secret_here"  # Cambia esto por una clave secreta segura

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
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return True
    except:
        return False

@app.route('/DevOps', methods=['POST'])
@require_apikey
def devops():
    jwt_token = request.headers.get('X-JWT-KWY')
    if not jwt_token or not verify_jwt(jwt_token):
        return jsonify({"error": "Invalid JWT"}), 401

    data = request.json
    if not all(key in data for key in ["message", "to", "from", "timeToLifeSec"]):
        return jsonify({"error": "Missing required fields"}), 400

    response = {
        "message": f"Hello {data['to']} your message will be send"
    }
    return jsonify(response)

@app.route('/<path:path>', methods=['GET', 'PUT', 'DELETE', 'PATCH'])
def catch_all(path):
    return "ERROR", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)