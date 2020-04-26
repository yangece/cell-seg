# Copyright (c) General Electric Company, 2017.  All rights reserved.

# Prototype code for testing rt106GenericAdaptorREST.py

import unittest
import sys
print(sys.argv)
idx = sys.argv.index('testGenericAdaptorAPIs.py')
sys.argv = sys.argv[idx:]

from rt106GenericAdaptorREST import app

class TestGenericAPIs(unittest.TestCase):

    def setUp(self):     # NOSONAR
        self.app = app.test_client()

    def test_not_found(self):
        url = 'http://localhost:7106/invalidinput'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_bad_request(self):
        url = 'http://localhost:7106/?'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_status(self):
        url = 'http://localhost:7106/'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_v1status(self):
        url = 'http://localhost:7106/v1'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_api(self):
        url = 'http://localhost:7106/v1/api'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_parameters(self):
        url = 'http://localhost:7106/v1/parameters'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_results(self):
        url = 'http://localhost:7106/v1/results'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_display(self):
        url = 'http://localhost:7106/v1/results/display'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_queue(self):
        url = 'http://localhost:7106/v1/queue'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_documentation(self):
        url = 'http://localhost:7106/v1/documentation'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_classification(self):
        url = 'http://localhost:7106/v1/classification'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
