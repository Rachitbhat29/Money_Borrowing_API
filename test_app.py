import unittest
import flask.globals
from main_app import app

import json
app.testing = True

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()

    def tearDown(self):
        self.ctx.pop()

    def test_login_endpoint(self):
        ''' Checking whether response is 200'''

        payload = json.dumps({"username": "rachit","password": "rachit123"})

        response = self.client.post("/login", headers={"Content-Type": "application/json"},data=payload)
        assert response.status_code == 200

    def test_login_response(self):
        '''check if response is ok'''
        payload = json.dumps({"username": "rachit","password": "rachit123"})

        response = self.client.post("/login", headers={"Content-Type": "application/json"},data=payload)

        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data.get("Msg"), "Login Successful")


    def test_request_content(self):
        '''check if content return is application/json'''
        tester = app.test_client(self)
        response = tester.get("/get_transactions")
        self.assertEqual(response.content_type, "application/json")


if __name__ == "__main__":
    unittest.main()