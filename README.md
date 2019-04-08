# QCM app


Simple Quizz application, one single python file.

## v0.1: proof of concept

### example

http://pascalmolin.pythonanywhere.com

### usage

```
$ python app.py server --allow-register
```

launches a webserver on ``localhost:5000``,
with a valid link to generate token.

```
$ python app.py server --help

Usage: app.py server [OPTIONS]

Options:
--debug                        turn on Flask debug mode
--verbose                      log requests
--allow-register               provide registration link at index page
--number_questions INTEGER     number of questions per quizz
--number_choices INTEGER       number of choices per question
--secret_key TEXT              secret key
--token_method [none|default]  token method
--help                         Show this message and exit.
```

### requirements

```
flask
itsdangerous
pyqrcode
click
```

### how it works

- for each _user_ an _assignment_ is generated
  from a list of possible _questions_.
  The anwsers are stored.

- all this is currently handled with a stupid database
  made of python lists and classes

- each action (see question, answer it, validate...)
  must be allowed by a valid token, which contains a
  signed version of
  - quizz id
  - user id
  - question id
  - expiration time

- a minimal flask setup makes this possible

### questions files

one yaml file, structured as follows

```
---
text: This question is
choices:
- { text: "easy", correct: True }
- { text: "impossible" }
- { text: "red" }
tag: [stupid]
```

(may add fields id, title, image, hints... they are ignored)

## todo

- images,...
- sql database

# Troubleshooting

### no qrcode under wsgi

see https://github.com/unbit/uwsgi/issues/1126
for python >= 3.6, configuration ``wsgi.ini`` needs option ``wsgi-disable-file-wrapper = true``
