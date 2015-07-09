#! /usr/bin/env python3

from functools import partial
from marshmallow import Schema, fields

import config
from models.odie import Order
from odie import ClientError

CashBoxField = partial(fields.Str, required=True, validate=lambda s: s in config.FS_CONFIG['CASH_BOXES'])
PrinterField = partial(fields.Str, required=True, validate=lambda s: s in config.FS_CONFIG['PRINTERS'])

def serialize(data, schema, many=False):
    res = schema().dump(data, many)
    if res.errors:
        raise ClientError(*res.errors)
    else:
        return res.data


class IdSchema(Schema):
    id = fields.Int(required=True)


class UserLoadSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)


class UserDumpSchema(Schema):
    username = fields.Str()
    first_name = fields.Str()
    last_name = fields.Str()


class DocumentDumpSchema(IdSchema):
    lectures = fields.List(fields.Nested(IdSchema))
    examinants = fields.List(fields.Nested(IdSchema))
    date = fields.Date()
    number_of_pages = fields.Int()
    solution = fields.Str()
    comment = fields.Str()
    document_type = fields.Str()
    available = fields.Method('is_available_for_printing')
    validated = fields.Boolean()
    validation_time = fields.Date()
    submitted_by = fields.Str()

    @staticmethod
    def is_available_for_printing(obj):
        return obj.file_id is not None


class ExaminantSchema(IdSchema):
    name = fields.Str()
    validated = fields.Boolean()


class OrderLoadSchema(Schema):
    name = fields.Str(required=True)
    document_ids = fields.List(fields.Int(), required=True)

    def make_object(self, data):
        try:
            return Order(name=data['name'],
                         document_ids=data['document_ids'])
        except KeyError:
            return None


class OrderDumpSchema(IdSchema):
    name = fields.Str()
    documents = fields.List(fields.Nested(DocumentDumpSchema))
    creation_time = fields.Date()


class LectureDumpSchema(IdSchema):
    name = fields.Str()
    aliases = fields.List(fields.Str())
    subject = fields.Str()
    comment = fields.Str()
    validated = fields.Boolean()


class LectureLoadSchema(Schema):  # used by student document submission
    name = fields.Str(required=True)
    subject = fields.Str(required=True)


class DocumentLoadSchema(Schema):  # used by student document submission
    lectures = fields.List(fields.Nested(LectureLoadSchema), required=True)
    examinants = fields.List(fields.Str, required=True)
    date = fields.Date(required=True)
    number_of_pages = fields.Int(required=True, validate=lambda n: n > 1)
    document_type = fields.Str(required=True, validate=lambda t: t in ['oral', 'oral reexam'])
    student_name = fields.Str(required=True)


class DepositDumpSchema(IdSchema):
    price = fields.Int()
    name = fields.Str()
    date = fields.Date()
    lectures = fields.List(fields.Str())


class DepositLoadSchema(IdSchema):
    cash_box = CashBoxField()


class PrintJobLoadSchema(Schema):
    cover_text = fields.Str(required=True)
    cash_box = CashBoxField()
    document_ids = fields.List(fields.Int(), required=True)
    deposit_count = fields.Int(required=True)
    printer = PrinterField()


class DonationLoadSchema(Schema):
    amount = fields.Int(required=True, validate=lambda i: i != 0)
    cash_box = CashBoxField()


class ErroneousSaleLoadSchema(Schema):
    amount = fields.Int(required=True, validate=lambda i: i > 0)
    cash_box = CashBoxField()

