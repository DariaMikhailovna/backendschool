#!/usr/bin/env python3

from flask import Flask, jsonify, abort, request, make_response
from pymongo import MongoClient, errors
import numpy as np
from collections import defaultdict
import datetime
from flask_expects_json import expects_json

app = Flask(__name__, static_url_path='')

client = MongoClient('localhost', 27017)
db = client.BSdb
import_collection = db.Imports
counters_collection = db.Counters

if not counters_collection.find_one({'id': 0}):
    db.Counters.insert_one(
        {
            'collection': 'Imports',
            'id': 0
        }
    )

citizen_properties = {
    'town': {'type': 'string', 'maxLength': 256, 'pattern': r'.*\w.*'},
    'street': {'type': 'string', 'maxLength': 256, 'pattern': r'.*\w.*'},
    'building': {'type': 'string', 'maxLength': 256, 'pattern': r'.*\w.*'},
    'apartment': {'type': 'number', "minimum": 0},
    'name': {'type': 'string', 'minLength': 1, 'maxLength': 256},
    'birth_date': {'type': 'string', 'pattern': r'\d\d\.\d\d\.\d\d\d\d'},
    'gender': {'enum': ['male', 'female']},
    'relatives': {
        'type': 'array',
        'items': {'type': 'number'},
        'uniqueItems': True
    }
}

citizen_properties_with_id = dict(citizen_properties, citizen_id={'type': 'number', "minimum": 0})

import_schema = {
    'type': 'object',
    'properties': {
        'citizens': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': citizen_properties_with_id,
                'additionalProperties': False,
                'minProperties': 9
            }
        }
    },
    'additionalProperties': False,
    'minProperties': 1
}

citizen_update_schema = {
    'type': 'object',
    'properties': citizen_properties,
    'additionalProperties': False
}


def insert_import(imp):
    imp['_id'] = db.Counters.find_and_modify(
        query={'collection': 'Imports'},
        update={'$inc': {'id': 1}},
        fields={'id': 1, '_id': 0},
        new=True
    ).get('id')
    imp['import_id'] = imp['_id']
    try:
        import_collection.insert_one(imp)
    except errors.DuplicateKeyError as e:
        insert_import(imp)
    return imp['import_id']


def validate_birth_date(date):
    numbers = list(map(int, date.split('.')))
    try:
        date = datetime.date(numbers[2], numbers[1], numbers[0])
        if date >= datetime.date.today():
            abort(400)
    except ValueError:
        abort(400)


def validate_relatives_and_ids(citizens):
    relatives_by_id = {citizen['citizen_id']: set(citizen['relatives']) for citizen in citizens}
    if len(relatives_by_id) != len(citizens):
        abort(400)
    for citizen in citizens:
        for id in citizen['relatives']:
            if id not in relatives_by_id:
                abort(400)
            if citizen['citizen_id'] not in relatives_by_id[id]:
                abort(400)


def calculate_age(born):
    today = datetime.datetime.utcnow()
    didnt_have_birthday_this_year = ((today.month, today.day) < (int(born[3:5]), int(born[0:2])))
    return today.year - int(born[6:10]) - didnt_have_birthday_this_year


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


# 1 - Принимает на вход набор с данными о жителях в формате json  и сохраняет его с уникальным идентификатором
@app.route('/imports', methods=['POST'])
@expects_json(import_schema)
def create_import():
    if not request.json:
        abort(400)
    imprt = request.json
    citizens = request.json['citizens']
    for citizen in citizens:
        date = citizen['birth_date']
        validate_birth_date(date)
    validate_relatives_and_ids(citizens)
    return jsonify({'data': {'import_id': insert_import(imprt)}}), 201


# 2 - Изменяет информацию о жителе в указанном наборе данных
@app.route('/imports/<int:import_id>/citizens/<int:citizen_id>', methods=['PATCH'])
@expects_json(citizen_update_schema)
def update_citizen_from_import(import_id, citizen_id):
    imprt = import_collection.find_one({'import_id': import_id})
    citizen_ids = set(map(lambda t: t['citizen_id'], imprt['citizens']))
    if not imprt:
        abort(404)
    if 'birth_date' in request.json:
        validate_birth_date(request.json['birth_date'])
    if 'relatives' in request.json:
        relatives = request.json['relatives']
        for id in relatives:
            if id not in citizen_ids:
                abort(400)
        new_rel_ids = set(relatives)
        old_rel_ids = set(import_collection.find_one({'import_id': import_id, 'citizens.citizen_id': citizen_id},
                                                     {'citizens.$': 1})['citizens'][0]['relatives'])
        for id in old_rel_ids - new_rel_ids:
            import_collection.update_one({'import_id': import_id, 'citizens.citizen_id': id},
                                         {'$pull': {'citizens.$.relatives': citizen_id}})
        for id in new_rel_ids - old_rel_ids:
            import_collection.update_one({'import_id': import_id, 'citizens.citizen_id': id},
                                         {'$addToSet': {'citizens.$.relatives': citizen_id}})
    for field in request.json:
        import_collection.update_one({'import_id': import_id, 'citizens.citizen_id': citizen_id},
                                     {'$set': {'citizens.$.' + str(field): request.json[field]}}, False, True)
    citizen = import_collection.find_one({'import_id': import_id, 'citizens.citizen_id': citizen_id},
                                         {'citizens.$': 1})['citizens'][0]
    return jsonify({'data': citizen}), 200


# 3 - Возвращает список всех жителей для указанного набора данных
@app.route('/imports/<int:import_id>/citizens', methods=['GET'])
def get_citizens_from_import(import_id):
    imprt = import_collection.find_one({'import_id': import_id})
    if not imprt:
        abort(404)
    return jsonify({'data': imprt['citizens']}), 200


# 4 - Возвращает жителей и количество подарков, которые они будут покупать своим ближайшим родственникам
@app.route('/imports/<int:import_id>/citizens/birthdays', methods=['GET'])
def get_birthdays(import_id):
    imprt = import_collection.find_one({'import_id': import_id})
    if not imprt:
        abort(404)
    d = {str(month): defaultdict(int) for month in range(1, 13)}
    for citizen in imprt['citizens']:
        cur_d = d[str(int(citizen['birth_date'][3:5]))]
        for relative_id in citizen['relatives']:
            cur_d[relative_id] += 1
    result = {month: [{'citizen_id': id, 'presents': cur_d[id]} for id in cur_d] for month, cur_d in d.items()}
    return jsonify({'data': result}), 200


# 5 - Возвращает статистику по городам для указанного набора данных в разрезе возраста жителей
@app.route('/imports/<int:import_id>/towns/stat/percentile/age', methods=['GET'])
def get_statistics(import_id):
    imprt = import_collection.find_one({'import_id': import_id})
    if not imprt:
        abort(404)
    d = defaultdict(list)
    for citizen in imprt['citizens']:
        d[citizen['town']].append(calculate_age(citizen['birth_date']))
    res = []
    for key, val in d.items():
        arr = np.array(val)
        p50 = np.percentile(arr, 50, interpolation='linear')
        p75 = np.percentile(arr, 75, interpolation='linear')
        p99 = np.percentile(arr, 99, interpolation='linear')
        res.append({'town': key, 'p50': format(p50, '.2f'), 'p75': format(p75, '.2f'), 'p99': format(p99, '.2f')})

    return jsonify({'data': res}), 200


if __name__ == '__main__':
    app.run(debug=True)
