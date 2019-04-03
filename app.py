#!/usr/bin/python

#####################################################################
#
# Databases
#
#####################################################################

import time
import random

class User(dict):
    """
    name
    date
    """
    def __init__(self, name):
        self['name'] = name
        self['date'] = time.time()

class Answers(list):
    """
    user
    quizz id
    score
    list choices
    """
    def __init__(self, uid, qid, quizz):
        self.score = None
        self.uid = uid
        self.qid = qid
        self.confirmed = False
        for question, choices in quizz:
            self.append(None)
    def set_choice(self, number, choice):
        self[number] = choice
    def set_score(self, score):
        self.score = score
class Choice:
    """
    text
    comment
    """
    def __init__(self, **kwargs):
        self.text = kwargs.get('text','')
        self.comment = kwargs.get('comment','')
        self.correct = kwargs.get('correct',False)
class Question(list):
    """
    title
    text
    list of choices
    index correct
    """
    def __init__(self, **kwargs):
        self.title = kwargs.get('title','')
        self.text =  kwargs.get('text','')
        self.correct = None
        for i,c in enumerate(kwargs.get('choices',[])):
            c = Choice(**c)
            self.append(c)
            if c.correct:
                assert self.correct == None, """ current implementation assumes there is only one correct answer per question """
                self.correct = i
        assert self.correct != None, """ missing correct answer in question %s """ % self.text
    def grade(self, cid):
        """ cid a choice index, is choice number cid correct ? """
        return self.correct == cid

class Quizz(list):
    """
    list of (questions, [index of choices])
    """
    pass

class WebQuestion(Question):
    def __init__(self, info, question, choices, selected = None):
        (uid,aid,number) = info
        self.info = info
        self.title = question.title
        self.number = number
        self.text = question.text
        for cid in choices:
            #choice = WebChoice(question[cid])
            self.append(question[cid])
        self.selected = selected

class WebConfirm(list):
    def __init__(self, info, user):
        list.__init__(self, info)
        self.info = info
        self.user = user

class WebScore(list):
    def __init__(self, info, user, answers):
        list.__init__(self, info)
        self.info = info
        self.user = user
        self.answers = answers

class QuizzApp:

    usersdb = []
    answersdb = []
    questionsdb = []
    quizzdb = []

    def __init__(self):
        pass

    def get_answer(self, aid):
        return self.answersdb[aid]
    def get_user(self, uid):
        return self.usersdb[uid]
    def get_question(self, qid):
        return self.questionsdb[qid]
    def get_quizz(self, qid):
        return self.quizzdb[qid]

    def get_entry(self, db, index):
        assert index < len(db), """ illegal index %i in table %s """ % (index, db.__name__) 
        return db[index]

    def add_entry(self, db, entry):
        db.append(entry)
        return len(db) - 1

    def add_quizz(self, quizz):
        self.quizzdb.append(quizz)
        return len(self.quizzdb) - 1
    def add_assignment(self, answers):
        self.answersdb.append(answers)
        return len(self.quizzdb) - 1

    def new_user(self, name):
        return self.add_entry(self.usersdb, User(name))

    def new_quizz(self,length=3,maxanswers=3):
        """
        generates a new random quizz
        """
        quizz = Quizz()
        pool = len(self.questionsdb)
        for iq in random.sample(xrange(pool), length):
            q = self.get_question(iq)
            # choose some choices, the first one is correct
            assert q.correct == 0, """ implementation assumes correct answer comes first, here correct = %i in question %s """ % (q.correct, q.text)
            c = random.sample(xrange(1,len(q)), maxanswers - 1)
            c.append(0)
            random.shuffle(c)
            quizz.append( (iq, c) )

        return self.add_quizz(quizz)

    def new_assignment(self, uid, qid):
        quizz = self.get_quizz(qid)
        answers = Answers(uid, qid, quizz)
        return self.add_assignment(answers)

    def post_answer(self, info, choice):
        uid, aid, number = info
        #user,answers,question = self.parse_token(token)
        answers = self.get_answer(aid)
        assert number < len(answers), """ wrong number %i >= len(assignment) """ % number
        if answers.confirmed:
            return None
        answers.set_choice(number, choice)
        return (uid,aid,number+1)

        #return self.get_question_data(self, (uid,aid,number+1))

    def post_confirmation(self, info):
        uid, aid = info
        #user,answers,question = self.parse_token(token)
        answers = self.get_answer(aid)
        answers.confirmed = True
        return self.get_score_data(info)

    def get_question_data(self, info):
        """
        info contains uid, aid, number
        returns the question data,
        If number > number of questions,
        return confirmation page or score instead.
        """
        uid, aid, number = info
        #user = self.get_user(uid)
        answers = self.get_answer(aid)
        quizz = self.get_quizz(answers.qid)

        if number >= len(answers):
            return self.get_score_data((uid,aid))

        qid, cid = quizz[number]
        question = self.get_question(qid)
        return WebQuestion(info, question, cid, answers[number])

    def grade(self, info):
        uid, aid = info
        user = self.get_user(uid)
        answers = self.get_answer(aid)
        quizz = self.get_quizz(answers.qid)
        score = 0
        for choice, (qid, cid) in zip(answers,quizz):
            print "choice %i in question %s"%(choice,(qid,cid))
            question = self.get_question(qid)
            score += question.grade(cid[choice])
        answers.set_score(score)

    def get_score_data(self, info):
        uid, aid = info
        user = self.get_user(uid)
        answers = self.get_answer(aid)
        if not answers.confirmed:
            return WebConfirm(info, user)
        if answers.score == None:
            self.grade(info)
        return WebScore(info, user, answers)

    def load_questions_yaml(self, filename):
        import yaml

        with open(filename, 'r') as stream:
            try:
                for q in yaml.load_all(stream):
                    q = Question(**q)
                    self.questionsdb.append(q)
            except yaml.YAMLError as exc:
                print(exc)

#####################################################################
# 
# Web server
#
#####################################################################

from flask import Flask, request, render_template, abort, redirect, url_for

from itsdangerous import (URLSafeTimedSerializer
                          as Serializer, BadSignature, SignatureExpired)

quizz = QuizzApp()
app = Flask('quizz')
app.config['SECRET_KEY'] = "lilalilalou"
app.config['number_questions'] = 5
app.config['number_choices'] = 3
METHOD='GET'

@app.template_filter('token')
def tokenize(data, salt='quizz',expiration=600):
    """
    creates a token for the given data
    """
    s = Serializer(app.config['SECRET_KEY'], salt = salt)
            #, expires_in = expiration)
    print "tokenize %s"%(data,)
    return s.dumps(data)

def load_token(token, salt=''):
    s = Serializer(app.config['SECRET_KEY'],salt=salt)
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None # valid token, but expired
    except BadSignature:
        return None # invalid token
    return data


@app.route('/')
def index():
    return render_template('register.html')
"""
a user token contains
- quizz: id
- user: id
plus a question number in order to answer that question
"""

from functools import wraps
def token_required(salt=''):
    def decorator(f):
        @wraps(f)
        def decorated(*args,**kwargs):
            if METHOD == 'POST':
                token = request.form.get('token')
            else:
                token = request.args.get('token')
            data = load_token(token, salt = salt)
            if data is None:
                return render_template("illegal.html"), 401
            return f(*args,data=data,**kwargs)
        return decorated
    return decorator

def redirect_token(route,data,salt=''):
    if data is None:
        return render_template('illegal.html')
    token = tokenize(data,salt=salt)
    return redirect(url_for(route, token=token))

def render_page(page):
    if isinstance(page, WebQuestion):
        return render_template('question.html', this=page)
    elif isinstance(page, WebConfirm):
        return render_template('confirm.html', this=page)
    elif isinstance(page, WebScore):
        return render_template('score.html', this=page)
    else:
        return render_template('illegal.html', this=page)

@app.route('/register', methods = [METHOD])
@token_required(salt='register')
def api_register(data=None):
    """ token data (registration key) """
    name = request.args.get('name')
    uid = quizz.new_user(name)
    qid = quizz.new_quizz(app.config['number_questions'],
                          app.config['number_choices'])
    aid = quizz.new_assignment(uid, qid)

    print "created user %i,quizz %i,assignment %i"%(uid,qid,aid)
    return redirect_token('api_question', (uid,aid,0), 'question')

@app.route('/question', methods = [METHOD])
@token_required(salt='question')
def api_question(data=None):
    """ token data (uid, aid, number) """
    page = quizz.get_question_data(data)
    return render_page(page)

@app.route('/score', methods = [METHOD])
@token_required(salt='score')
def api_score(data=None):
    """ token data (uid, aid, number) """
    page = quizz.get_score_data(data)
    return render_page(page)

@app.route('/answer', methods = [METHOD])
@token_required(salt='answer')
def api_answer(data=None):
    """ token data (uid, aid, number) """
    #choice = request.args.get('token')
    choice = int(request.args.get('choice'))
    data = quizz.post_answer(data, choice)
    return redirect_token('api_question', data, 'question')

@app.route('/submit', methods = [METHOD])
@token_required(salt='submit')
def api_submit(data=None):
    """ token data (uid, aid) """
    print 'received token %s' % data
    data = quizz.post_confirmation(data)
    return redirect_token('api_score', data, 'score')

import click

@click.group()
def cli():
    pass

@cli.command()
@click.option('--debug',default=True, help='turn on Flask debug mode')
def server(debug):
    app.run(debug=debug)

@cli.command()
@click.option('--yaml',default='questions.yaml',
        help='load questions file')
def build(yaml):
   print quizz.get_question_data((uid,aid,0))

if __name__ == '__main__':
    quizz.load_questions_yaml('questions.yaml')
    uid = quizz.new_user('Pascal')
    qid = quizz.new_quizz(1)
    aid = quizz.new_assignment(uid, qid)
    cli()
