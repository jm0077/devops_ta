import unittest
import json
import sys
import os

# Añadir el directorio src al path de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from app import app

class TestDevOpsEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.api_key = "2f5ae96c-b558-4c7b-a590-a501ae1c3f6c"
        self.jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U"

    def test_valid_request(self):
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

    def test_invalid_api_key(self):
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

    def test_invalid_method(self):
        response = self.app.get('/DevOps')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.decode(), "ERROR")

if __name__ == '__main__':
    unittest.main()