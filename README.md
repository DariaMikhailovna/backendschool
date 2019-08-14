# backendschool

Использованные внешние python-библиотеки:
1) flask: https://flask.palletsprojects.com/en/1.1.x/                       (сервер)
2) pymongo: https://api.mongodb.com/python/current/                         (база)
3) numpy: https://docs.scipy.org/doc/                                       (перцентили)
4) flask_expects_json: https://pypi.org/project/flask-expects-json/         (валидация)
5) pytest: https://docs.pytest.org/en/latest/contents.html                  (тесты)

Инструкция по развертыванию тестов:
1) Запустить app.py (если не подключена mongodb, то сначало подключить ее)
2) В терминале набрать: py.test -v
3) Ждать
4) FAILED - не прошло, PASSED - прошло
