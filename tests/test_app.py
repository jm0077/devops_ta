import unittest
import json
import sys
import os
import jwt
import redis
from unittest.mock import patch, Mock, mock_open
from datetime import datetime, timedelta

# Añadir el directorio src al path de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from app import app, JWT_SECRET

class TestDevOpsEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.api_key = "2f5ae96c-b558-4c7b-a590-a501ae1c3f6c"
        
        # Crear un token JWT válido que expire en 1 hora
        self.jwt_payload = {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "sub": "test",
            "timeToLifeSec": 3600
        }
        self.jwt = jwt.encode(self.jwt_payload, JWT_SECRET, algorithm="HS256")
        
        # Mock Redis client
        self.redis_patcher = patch('app.redis_client')
        self.mock_redis = self.redis_patcher.start()
        self.mock_redis.get.return_value = None

    def tearDown(self):
        self.redis_patcher.stop()

    def test_valid_request(self):
        """Test a completely valid request with all correct parameters"""
        headers = {
            "X-Parse-REST-API-Key": self.api_key,
            "X-JWT-KWY": self.jwt,
            "Content-Type": "application/json"
        }
        data = {
            "message": "This is a test",
            "to": "Juan Perez",
            "from": "Rita Asturia",
            "timeToLifeSec": 45
        }
        response = self.app.post('/DevOps', headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_data, {"message": "Hello Juan Perez your message will be send"})

    def test_missing_api_key(self):
        """Test request without API key"""
        headers = {
            "X-JWT-KWY": self.jwt,
            "Content-Type": "application/json"
        }
        data = {
            "message": "This is a test",
            "to": "Juan Perez",
            "from": "Rita Asturia",
            "timeToLifeSec": 45
        }
        response = self.app.post('/DevOps', headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_data, {"error": "Invalid API Key"})

    def test_invalid_api_key(self):
        """Test request with invalid API key"""
        headers = {
            "X-Parse-REST-API-Key": "invalid_key",
            "X-JWT-KWY": self.jwt,
            "Content-Type": "application/json"
        }
        data = {
            "message": "This is a test",
            "to": "Juan Perez",
            "from": "Rita Asturia",
            "timeToLifeSec": 45
        }
        response = self.app.post('/DevOps', headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_data, {"error": "Invalid API Key"})

    def test_missing_jwt(self):
        """Test request without JWT token"""
        headers = {
            "X-Parse-REST-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "message": "This is a test",
            "to": "Juan Perez",
            "from": "Rita Asturia",
            "timeToLifeSec": 45
        }
        response = self.app.post('/DevOps', headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_data, {"error": "Missing JWT"})

    def test_expired_jwt(self):
        """Test request with expired JWT token"""
        # Create expired token
        expired_payload = {
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(hours=2),
            "sub": "test",
            "timeToLifeSec": 3600
        }
        expired_jwt = jwt.encode(expired_payload, JWT_SECRET, algorithm="HS256")
        
        headers = {
            "X-Parse-REST-API-Key": self.api_key,
            "X-JWT-KWY": expired_jwt,
            "Content-Type": "application/json"
        }
        data = {
            "message": "This is a test",
            "to": "Juan Perez",
            "from": "Rita Asturia",
            "timeToLifeSec": 45
        }
        response = self.app.post('/DevOps', headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertIn("Token expired", response_data.get("error", ""))

    def test_invalid_jwt_signature(self):
        """Test request with JWT token signed with wrong key"""
        invalid_jwt = jwt.encode(self.jwt_payload, "wrong_secret", algorithm="HS256")
        
        headers = {
            "X-Parse-REST-API-Key": self.api_key,
            "X-JWT-KWY": invalid_jwt,
            "Content-Type": "application/json"
        }
        data = {
            "message": "This is a test",
            "to": "Juan Perez",
            "from": "Rita Asturia",
            "timeToLifeSec": 45
        }
        response = self.app.post('/DevOps', headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertIn("Invalid token", response_data.get("error", ""))

    def test_reused_jwt(self):
        """Test request with previously used JWT token"""
        self.mock_redis.get.return_value = "used"
        
        headers = {
            "X-Parse-REST-API-Key": self.api_key,
            "X-JWT-KWY": self.jwt,
            "Content-Type": "application/json"
        }
        data = {
            "message": "This is a test",
            "to": "Juan Perez",
            "from": "Rita Asturia",
            "timeToLifeSec": 45
        }
        response = self.app.post('/DevOps', headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertIn("Token already used", response_data.get("error", ""))

    def test_missing_required_fields(self):
        """Test request with missing required fields in payload"""
        headers = {
            "X-Parse-REST-API-Key": self.api_key,
            "X-JWT-KWY": self.jwt,
            "Content-Type": "application/json"
        }
        data = {
            "message": "This is a test",
            # Missing 'to' field
            "from": "Rita Asturia",
            "timeToLifeSec": 45
        }
        response = self.app.post('/DevOps', headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_data, {"error": "Missing required fields"})

    def test_invalid_method(self):
        """Test invalid HTTP methods"""
        for method in ['GET', 'PUT', 'DELETE', 'PATCH']:
            response = getattr(self.app, method.lower())('/DevOps')
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response.data.decode(), "ERROR")

    def test_health_check(self):
        """Test health check endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_data, {"status": "healthy"})

    @patch('app.send_from_directory')
    def test_serve_validation_file(self, mock_send):
        """Test serving PKI validation files"""
        mock_send.return_value = "test content"
        response = self.app.get('/.well-known/pki-validation/testfile.txt')
        self.assertEqual(response.status_code, 200)
        mock_send.assert_called_once_with('/app/.well-known/pki-validation', 'testfile.txt')

    def test_catch_all_non_pki(self):
        """Test catch-all route for non-PKI paths"""
        paths = [
            '/',
            '/invalid',
            '/api/v1/something'
        ]
        for path in paths:
            response = self.app.get(path)
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response.data.decode(), "ERROR")

    def test_redis_exception_handling(self):
        """Test handling of Redis exceptions"""
        self.mock_redis.get.side_effect = redis.RedisError("Connection failed")
        
        headers = {
            "X-Parse-REST-API-Key": self.api_key,
            "X-JWT-KWY": self.jwt,
            "Content-Type": "application/json"
        }
        data = {
            "message": "This is a test",
            "to": "Juan Perez",
            "from": "Rita Asturia",
            "timeToLifeSec": 45
        }
        response = self.app.post('/DevOps', headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertIn("Connection failed", response_data.get("error", ""))

if __name__ == '__main__':
    unittest.main()