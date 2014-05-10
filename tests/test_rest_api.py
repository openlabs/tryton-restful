# -*- coding: utf-8 -*-
"""
    test_rest_api.py

    :copyright: (c) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import math
import base64
import unittest
from datetime import datetime
from decimal import Decimal

from flask import json, jsonify

from trytond import security
import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.tests.test_tryton import POOL, DB_NAME
from tryton_restful.application import app


app.config['TESTING'] = True


def get_auth_header():
    result = security.login(DB_NAME, 'admin', 'admin')
    return 'Basic ' + base64.b64encode('%s:%s' % result)


class TestRestfulApi(unittest.TestCase):
    """
    Test the rest api
    """
    @classmethod
    def setUpClass(cls):
        trytond.tests.test_tryton.install_module('ir')
        trytond.tests.test_tryton.install_module('res')

    def test_collection_get(self):
        with app.test_client() as c:
            result = c.get(
                '/%s/model/res.user' % DB_NAME,
                headers={'Authorization': get_auth_header()}
            )
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertEqual(len(data['items']), 1)

    def test_collection_get_domain(self):
        """
        GET with a domain
        """
        domain = [('module', '=', 'ir')]

        # Fetch result from tryton api first to compare with rest api
        with Transaction().start(DB_NAME, 0, readonly=True):
            IrModel = POOL.get('ir.model')
            count = IrModel.search_count(domain)

        with app.test_client() as c:
            result = c.get(
                '/%s/model/ir.model?domain=%s&per_page=1000' % (
                    DB_NAME, json.dumps(domain)
                ),
                headers={'Authorization': get_auth_header()}
            )
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertEqual(len(data['items']), count)

    def test_collection_get_pagination(self):
        """
        GET with a domain
        """
        # Fetch result from tryton api first to compare with rest api
        with Transaction().start(DB_NAME, 0, readonly=True):
            IrModel = POOL.get('ir.model')
            count = IrModel.search_count([])

        with app.test_client() as c:
            total_count = 0
            for page in xrange(1, 100):
                # Try to Iterate over a 100 pages
                result = c.get(
                    '/%s/model/ir.model?page=%d' % (DB_NAME, page),
                    headers={'Authorization': get_auth_header()}
                )
                page_count = len(json.loads(result.data)['items'])
                total_count += page_count
                if not page_count:
                    break

            # ensure that the total count matches
            self.assertEqual(total_count, count)

            # Ensure that the empty page is above the range
            self.assertEqual(page - 1, math.ceil(count / 10))

    def test_collection_get_order(self):
        """
        Ensure that the order is maintained
        """
        order = [('module', 'ASC'), ('id', 'DESC')]

        with Transaction().start(DB_NAME, 0, readonly=True):
            IrModel = POOL.get('ir.model')
            model_ids = map(int, IrModel.search([], order=order))

        with app.test_client() as c:
            result = c.get(
                '/%s/model/ir.model?order=%s&per_page=1000' % (
                    DB_NAME, json.dumps(order)
                ),
                headers={'Authorization': get_auth_header()}
            )
            self.assertEqual(
                [rec['id'] for rec in json.loads(result.data)['items']],
                model_ids
            )

    def test_collection_post(self):
        """
        Create a record using POST
        """
        with app.test_client() as c:
            values = {
                'name': 'New User Name',
                'login': 'new-user-name',
            }
            result = c.post(
                '/%s/model/res.user' % DB_NAME,
                data=json.dumps([values]),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': get_auth_header()
                }
            )
            self.assertEqual(result.status_code, 201)
            self.assertEqual(
                json.loads(result.data)['items'][0]['rec_name'], values['name']
            )

    def test_collection_delete(self):
        """
        Delete a collection
        """
        with app.test_client() as c:
            result = c.delete(
                '/%s/model/res.user' % DB_NAME,
                headers={'Authorization': get_auth_header()}
            )

            # The user record is created by xml, so this should blow up
            self.assertEqual(result.status_code, 500)
            self.assertEqual(
                json.loads(result.data)['error']['type'],
                'UserError'
            )

    def test_element_get(self):
        """
        Simple GET with a single record
        """
        with app.test_client() as c:
            result = c.get(
                '/%s/model/res.user/1' % DB_NAME,
                headers={'Authorization': get_auth_header()}
            )
            self.assertEqual(result.status_code, 200)
            user_1 = json.loads(result.data)
            self.assertEqual(user_1['name'], 'Administrator')

    def test_element_get_field_names(self):
        """
        Simple GET with a single record
        """
        with app.test_client() as c:
            result = c.get(
                '/%s/model/res.user/1?'
                'fields_names=name&fields_names=login' % DB_NAME,
                headers={'Authorization': get_auth_header()}
            )
            self.assertEqual(result.status_code, 200)
            user_1 = json.loads(result.data)
            self.assertEqual(user_1['name'], 'Administrator')
            self.assertEqual(
                set(user_1.keys()),
                set(['id', 'name', 'login'])
            )

    def test_element_put(self):
        with app.test_client() as c:
            values = {'email': 'admin@example.com'}
            result = c.put(
                '/%s/model/res.user/1' % DB_NAME,
                data=json.dumps(values),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': get_auth_header(),
                }
            )
            self.assertEqual(result.status_code, 200)
            user_1 = json.loads(result.data)
            self.assertEqual(user_1['email'], values['email'])

    def test_element_delete(self):
        """
        Try deleting the webdav module
        """
        with app.test_client() as c:
            webdav_module = c.get(
                '/%s/model/ir.module.module?domain=%s' % (
                    DB_NAME, json.dumps([('name', '=', 'webdav')])
                ),
                headers={'Authorization': get_auth_header()}
            )
            module_id = json.loads(webdav_module.data)['items'][0]['id']
            result = c.delete(
                '/%s/model/ir.module.module/%d' % (DB_NAME, module_id),
                headers={'Authorization': get_auth_header()}
            )
            self.assertEqual(result.status_code, 205)

    def test_login(self):
        """
        Check if login returns valid response
        """
        with app.test_client() as c:
            result = c.post(
                '/%s/login' % DB_NAME,
                data={'login': 'admin', 'password': 'wrong'}
            )
            self.assertEqual(result.status_code, 403)
            result = c.post(
                '/%s/login' % DB_NAME,
                data={'login': 'admin', 'password': 'admin'}
            )
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertTrue('id' in data)
            self.assertTrue('session' in data)

    def test_session(self):
        """
        Test that wrong authentication returns 401
        """
        with app.test_client() as c:
            result = c.get(
                '/%s/model/res.user' % DB_NAME,
                headers={'Authorization': 'an-invalid-session'}
            )
            self.assertEqual(result.status_code, 302)

    def test_json_encoding(self):
        """
        Ensure that the json encoding is tryton style
        """
        with app.test_request_context('/'):
            value = {
                u'dt': datetime(2014, 5, 10, 16, 47, 26),
                u'num': Decimal('10.12345'),
            }
            dump = jsonify(value).data
            self.assertEqual(json.loads(dump), value)


def suite():
    """
    Define suite
    """
    test_suite = unittest.TestSuite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestRestfulApi)
    )
    return test_suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
