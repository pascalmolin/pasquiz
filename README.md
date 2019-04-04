# QCM app


Simple Quizz application, one single python file.

## v0.1: proof of concept

## usage

```
python app.py
```

launches a webserver on ``localhost:5000``.

Then go to /token to obtain a valid token

Go to /token to get a valid token and 

The toplevel page

## how it works

- 

- a stupid database with python lists and dicts

just a flask app

## questions files

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

## app

## todo


### sql database

- questions

- choices

- quizz

  | qid | title | text | choices | correct |
  |-----|-------|------|---------|---------|
  | int | text  | text | int     | int     |

- users: uid, name, date

  | uid | number | date |
  |-----|--------|------|
  | int | int    | int  |

- answers

  | uid | number | cid |
  |-----|--------|-----|
  | int | int    | int |

- choices table

  | qid | cid | text | comment |
  |-----|-----|------|---------|
  | int | int | text | text    |

## Quizz pages

generated 

each page contains a token field, which contains an encrypted version of
- quizz id
- user id
- question id
- expiration time

on reply, the corresponding answer entry is recorded.

the page also contains a secure (and permanent) link to access 
the score.

## server




