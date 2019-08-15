import pytest
import requests
import json
from pymongo import MongoClient, errors


client = MongoClient('localhost', 27017)
db = client.BSdb
import_collection = db.Imports
counters_collection = db.Counters
import_collection.remove({})
counters_collection.remove({})
db.Counters.insert_one(
    {
        'collection': 'Imports',
        'id': 0
    }
)


def test_first():
    url = 'http://localhost:5000/imports'
    data = {
        "citizens": [{
            "citizen_id": 1,
            "town": "Москва",
            "street": "Льва Толстого",
            "building": "16к7стр5",
            "apartment": 7,
            "name": "Иванов Иван Иванович",
            "birth_date": "01.02.2000",
            "gender": "male",
            "relatives": [2]
        },
            {
                "citizen_id": 2,
                "town": "Питер",
                "street": "Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Приходько Анна Анатольевна",
                "birth_date": "10.11.1986",
                "gender": "female",
                "relatives": [1]
            },
            {
                "citizen_id": 3,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Фефер Иван Иванович",
                "birth_date": "03.02.1953",
                "gender": "male",
                "relatives": []
            }
        ]
    }
    resp = requests.post(url, json=data)
    status = resp.status_code
    assert (status == 201)


def test_second():
    url = 'http://localhost:5000/imports/1/citizens/1'
    data = {
            "town": "Москва",
            "street": "Льва Толстого",
            "building": "16к7стр5",
            "apartment": 7,
            "name": "Иванов Иван Иванович",
            "birth_date": "01.02.2000",
            "gender": "male",
            "relatives": []
    }
    resp = requests.patch(url, json=data)
    status = resp.status_code
    assert (status == 200)


def test_third():
    url = 'http://localhost:5000/imports/1/citizens'
    resp = requests.get(url)
    status = resp.status_code
    assert(status == 200)


def test_fourth():
    url = 'http://localhost:5000/imports/1/citizens/birthdays'
    resp = requests.get(url)
    # my_json = json.loads(resp.text)
    status = resp.status_code
    assert (status == 200)


def test_fifth():
    url = 'http://localhost:5000/imports/1/towns/stat/percentile/age'
    resp = requests.get(url)
    # my_json = json.loads(resp.text)
    status = resp.status_code
    assert (status == 200)


if __name__ == '__main__':
    test_third()
