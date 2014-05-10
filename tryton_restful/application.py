# -*- coding: utf-8 -*-
"""
    application.py

    :copyright: (c) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import traceback
from functools import wraps, partial

from flask import (
    Flask, Blueprint, request, jsonify, current_app, Response,
    g, url_for, redirect, json)
from trytond import backend, security
from trytond.pool import Pool
from trytond.cache import Cache
from trytond.config import CONFIG
from trytond.exceptions import UserError
from trytond.transaction import Transaction
from trytond.protocols.jsonrpc import JSONEncoder, object_hook

restful = Blueprint('restful', __name__)

app = Flask(__name__)


app.json_decoder = partial(json.JSONDecoder, object_hook=object_hook)
app.json_encoder = JSONEncoder


def after_this_request(f):
    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f


@app.after_request
def call_after_request_callbacks(response):
    for callback in getattr(g, 'after_request_callbacks', ()):
        callback(response)
    return response


class TrytonAuth(object):
    """
    Extend BasicAuth to use sessions
    """
    @classmethod
    def verify_session(cls, database, user, session):
        """
        Return the result from the verification of a session
        """
        try:
            return security.check(database, int(user), session)
        except Exception:
            return None

    @classmethod
    def unauthorized(cls):
        header = 'Basic realm="%s"' % request.view_args['database']
        return Response(
            'Unauthorized', 401,
            {'WWW-Authenticate': header}
        )

    @classmethod
    def login_required(cls, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            database = kwargs['database']
            if request.authorization:
                auth = request.authorization
                response = cls.verify_session(
                    database, auth.username, auth.password
                )
                if response is not None:
                    g.current_user = response
                    return f(*args, **kwargs)
            return redirect(url_for('restful.login', database=database))
        return wrapper


def transaction(function):
    """
    Handles a transaction as a decorator.

    Database View Argument
    ~~~~~~~~~~~~~~~~~~~~~~

    The database view argument originates from the string converter in the
    url_prefix used when registering the blueprint.
    The database argument is then popped out by the this decorator and the
    view function is not passed

    Readonly
    ~~~~~~~~

    All GET requests are considered readonly and are executed under a readonly
    transaction

    Exception Handling
    ~~~~~~~~~~~~~~~~~~

    All exceptions during the wrapped method call are silently converted into
    a 500 response with the error as the json body.
    """
    @wraps(function)
    def wrapper(database, *args, **kwargs):
        DatabaseOperationalError = backend.get('DatabaseOperationalError')

        Cache.clean(database)

        # Intialise the pool. The init method is smart enough not to
        # reinitialise if it is already initialised.
        Pool(database).init()

        # get the context from the currently logged in user
        with Transaction().start(database, g.current_user, readonly=True):
            User = Pool().get('res.user')
            context = User.get_preferences(context_only=True)

        readonly = request.method == 'GET'

        for count in range(int(CONFIG['retry']), -1, -1):
            with Transaction().start(
                    database, g.current_user,
                    readonly=readonly,
                    context=context) as transaction:
                cursor = transaction.cursor
                try:
                    result = function(*args, **kwargs)
                    if not readonly:
                        cursor.commit()
                except DatabaseOperationalError, exc:
                    cursor.rollback()
                    if count and not readonly:
                        continue
                    result = jsonify(error=unicode(exc)), 500
                except UserError, exc:
                    cursor.rollback()
                    result = jsonify(error={
                        'type': 'UserError',
                        'message': exc.message,
                        'description': exc.description,
                        'code': exc.code,
                    }), 500
                    current_app.logger.error(traceback.format_exc())
                except Exception, exc:
                    cursor.rollback()
                    result = jsonify(error=unicode(exc)), 500
                    current_app.logger.error(traceback.format_exc())
                else:
                    if not (readonly or current_app.testing):
                        cursor.commit()

            Cache.resets(database)
            return result
    return wrapper


ar_to_dict = lambda ar: {'id': ar.id, 'rec_name': ar.rec_name}


@restful.route('/login', methods=['POST'])
def login(database):
    """
    POST: Login and return user id and session
    """
    result = security.login(
        database, request.form['login'], request.form['password']
    )
    if result:
        return jsonify({
            'id': result[0],
            'session': result[1],
        })
    return 'Bad Username or Password', 403


@restful.route('/model/<model>', methods=['GET', 'POST', 'DELETE'])
@TrytonAuth.login_required
@transaction
def collection(model):
    """
    GET: List the URIs

    POST
    ~~~~

    Create a new entry(ies) in the model from data in JSON body.
    Remember that the body should be a list of dictionaries.


    DELETE: Delete all the records
    """
    model = Pool().get(model, type='model')

    if request.method == 'GET':
        domain = json.loads(
            request.args.get('domain', '[]')
        )

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        offset = (page - 1) * per_page
        limit = per_page

        order = None
        if 'order' in request.args:
            order = json.loads(request.args['order'])

        return jsonify(
            items=map(ar_to_dict, model.search(domain, offset, limit, order))
        )

    elif request.method == 'POST':
        return jsonify(
            items=map(ar_to_dict, model.create(request.json))
        ), 201

    elif request.method == 'DELETE':
        model.delete(model.search([]))
        return jsonify({}), 205


@restful.route('/model/<model>/<int:record_id>',
               methods=['GET', 'PUT', 'DELETE'])
@TrytonAuth.login_required
@transaction
def element(model, record_id):
    """
    GET: Retrieve a representation of the member
    PUT: Write to the record
    DELETE: Delete the record

    :param model: name of the model
    :param record_id: ID of the record
    """
    model = Pool().get(model, type='model')
    record = model(record_id)

    if request.method == 'GET':
        # Return a dictionary of the read record
        fields_names = request.args.getlist('fields_names')
        return jsonify(
            model.read([record.id], fields_names)[0]
        )

    elif request.method == 'PUT':
        # Write to the record and return the updated record
        model.write([record], request.json)
        fields_names = request.args.getlist('fields_names')
        return jsonify(
            model.read([record.id], fields_names)[0]
        )

    elif request.method == 'DELETE':
        model.delete([record])
        return jsonify({}), 205


app.register_blueprint(restful, url_prefix='/<database>')
