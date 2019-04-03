# QCM app


## structured data

input as yaml

---
id: exercise id
title: exercice title
question: required
hints: optional
answers:
-
  text: required
  correct: true/false
  clue: optional
-
  text: required

## sql data

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




