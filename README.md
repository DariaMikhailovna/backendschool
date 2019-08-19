# backendschool

Использованные внешние python-библиотеки:
1) flask: https://flask.palletsprojects.com/en/1.1.x/                       (сервер)
2) pymongo: https://api.mongodb.com/python/current/                         (база)
3) numpy: https://docs.scipy.org/doc/                                       (перцентили)
4) flask_expects_json: https://pypi.org/project/flask-expects-json/         (валидация)
5) pytest: https://docs.pytest.org/en/latest/contents.html                  (тесты)

Инструкция по развертыванию тестов:
1) Установить pytest: $ pip install pytest==2.9.1 
2) Запустить app.py (если не запущена): $ python3 app.py
3) В терминале набрать: py.test -v
4) Ждать
5) FAILED - не прошло, PASSED - прошло
