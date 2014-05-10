# -*- coding: utf-8 -*-
"""
    tests/__init__.py

    :copyright: (c) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import unittest

from tests.test_rest_api import suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
