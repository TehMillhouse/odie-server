#! /usr/bin/env python3

import config

from flask.ext.login import current_user, login_required
from marshmallow import fields, Schema
from marshmallow.validate import Length
from sqlalchemy.orm import subqueryload

from .common import IdSchema, DocumentDumpSchema
from odie import csrf
from api_utils import endpoint, api_route, serialize
from db.documents import Deposit
from db.odie import Order

## Routes may either return something which can be turned into json using
## flask.jsonify or a api_utils.PaginatedResult. The actual response is assembled
## in api_utils.api_route.

@api_route('/api/config')
def get_config():
    return config.FS_CONFIG


class UserDumpSchema(Schema):
    username = fields.Str()
    first_name = fields.Str()
    last_name = fields.Str()
    office = fields.Function(config.try_get_office)


class LoginDumpSchema(Schema):
    user = fields.Nested(UserDumpSchema)
    token = fields.Str()

# exempting this from CSRF is okay since the dangers of CSRF only apply to endpoints that do something
# whereas this simply returns some data. As long as CORS is set up correctly, we're fine

@api_route('/api/user_info')
@csrf.exempt
@login_required
def user_info():
    # Explicitly pass the csrf token cookie value for cross-origin clients.
    return serialize({'user': current_user, 'token': csrf._get_token()}, LoginDumpSchema)


class OrderDumpSchema(IdSchema):
    name = fields.Str()
    documents = fields.List(fields.Nested(DocumentDumpSchema))
    creation_time = fields.Date()


api_route('/api/orders', methods=['GET'])(
login_required(
endpoint(
        schemas={
            'GET': OrderDumpSchema,
        },
        query=Order.query)
))


class OrderLoadSchema(Schema):
    name = fields.Str(required=True, validate=Length(min=1))
    document_ids = fields.List(fields.Int(), required=True)

    def make_object(self, data):
        try:
            return Order(name=data['name'],
                         document_ids=data['document_ids'])
        except KeyError:
            return None


api_route('/api/orders', methods=['POST'])(
csrf.exempt(
endpoint(
        schemas={
            'POST': OrderLoadSchema,
        },
        query=None)
))

api_route('/api/orders/<int:instance_id>', methods=['GET', 'DELETE'])(
login_required(
endpoint(
        schemas={'GET': OrderDumpSchema},
        query=Order.query,
        allow_delete=True)
))


class DepositDumpSchema(IdSchema):
    price = fields.Int()
    name = fields.Str()
    date = fields.Date()
    lectures = fields.List(fields.Str())


api_route('/api/deposits')(
login_required(
endpoint(
        schemas={'GET': DepositDumpSchema},
        query=Deposit.query.options(subqueryload('lectures')))
))

