Tryton Restful
==============

A REST API for Tryton Models

Installation
------------

Install from python package index::

    pip install tryton-restful

Usage
-----

On installation you should be able to use the `tryton_restful` script which
runs a local development server.

.. code:: shell

   tryton_restful --help

    Usage: tryton_restful [OPTIONS] HOST PORT

      Runs the application on a local development server.

    Options:
      -c, --config TEXT            Path to tryton configuration file
      --debug
      --threaded / --not-threaded  should the process handle each request in a
                                   separate thread?
      --help                       Show this message and exit.

You can run the server by::

    tryton_restful -c /path/to/tryton/config


.. tip::

   You can also specify the config file using environment variables.

   export TRYTON-CONFIG=/path/to/tryton/config


Rest API Endpoints:
-------------------

/<dbname>/login
````````````````
===== ========================================================================
POST   Expects `login` and `password` as form data and returns a JSON of
       user ID and session to be used for subsequent requests
===== ========================================================================

.. code:: python

    import requests
    import json
    
    DATABASE_NAME = 'rest'
    BASE_PATH = 'http://localhost:9000/' + DATABASE_NAME
    
    login_result = requests.post(BASE_PATH + '/login', data={'login': 'admin', 'password': 'admin'})
    tryton_session = login_result.json()
    print tryton_session

.. parsed-literal::

    {u'session': u'966689963c0a4a939cb326c1451b0fe9', u'id': 1}


/<dbname>/model/<model.name>
````````````````````````````````

======== =====================================================================
GET      Return a list of records (Just the ID and rec_name)

         Params:

         * domain: JSON serialised domain expression
           example: `[['name', 'ilike', 'openlabs']]`
         * page: Integer number of the page
         * per_page: The number of records to be returned per page
         * order: JSON serialised order expression in which the records
           should be sorted. Ex: `[('name', 'ASC'), ('date', 'DESC')]`
======== =====================================================================

.. code:: python

    s = requests.Session()
    s.auth = (tryton_session['id'], tryton_session['session'])
    
    # Use the session and get the list of users
    print s.get(BASE_PATH + '/model/res.user').json()

.. parsed-literal::

    {u'items': [{u'rec_name': u'Administrator', u'id': 1}]}


======== =====================================================================
POST     Creates one or more records in the given model
======== =====================================================================

.. code:: python

    # Create a new user
    headers = {'content-type': 'application/json'}
    values = [
        {'name': 'Thomas', 'login': 'thomas', 'password': 'password'},
        {'name': 'Alfred', 'login': 'alfred', 'password': 'somethingelse'},
    ]
    users = s.post(BASE_PATH + '/model/res.user', data=json.dumps(values), headers=headers).json()
    print users

.. parsed-literal::

    {u'items': [{u'rec_name': u'Thomas', u'id': 3}, {u'rec_name': u'Alfred', u'id': 4}]}



======== =====================================================================
DELETE   Delete **all** records in the given model
======== =====================================================================


/<dbname>/model/<model.name>/<id>
``````````````````````````````````

======== =====================================================================
GET      Return the details of the given record

         Params:

         * fields_names: specify the list of fields to be returned.
           Default behavior is to return as much data as possible
======== =====================================================================

.. code:: python

    # Get full details of the first user
    print s.get(BASE_PATH + '/model/res.user/1').json()

.. parsed-literal::

    {u'create_date': u'Sat, 10 May 2014 08:51:16 GMT', ....}


.. code:: python

    # Get only a limited set of fields
    user_url = BASE_PATH + '/model/res.user/1'
    print s.get(user_url + '?fields_names=name&fields_names=email').json()

.. parsed-literal::

    {u'email': None, u'name': u'Administrator', u'id': 1}

======== =====================================================================
PUT      Update the given resource
======== =====================================================================

.. code:: python

    # Change the email of the user
    headers = {'content-type': 'application/json'}
    user_data = s.put(user_url, data=json.dumps({'email': 'admin@example.com'}), headers=headers).json()
    print user_data['email']

.. parsed-literal::

    admin@example.com

======== =====================================================================
DELETE   Delete the given record
======== =====================================================================

.. code:: python

    # get a new list of all users
    print s.get(BASE_PATH + '/model/res.user').json()

.. parsed-literal::

     {u'items': [{u'rec_name': u'Administrator', u'id': 1}, {u'rec_name': u'Thomas', u'id': 3}, {u'rec_name': u'Alfred', u'id': 4}]}


.. code:: python

    # delete user Alfred with ID 4
    print s.delete(BASE_PATH + '/model/res.user/4')

.. parsed-literal::

    <Response [205]>


.. code:: python

    # get a new list of all users
    print s.get(BASE_PATH + '/model/res.user').json()

.. parsed-literal::

    {u'items': [{u'rec_name': u'Administrator', u'id': 1}, {u'rec_name': u'Thomas', u'id': 3}]}
