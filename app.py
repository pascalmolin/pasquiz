#!/usr/bin/python

#####################################################################
#
# Databases
#
#####################################################################

import time
import random
import sys

if sys.version_info.major == 3:
    unicode = str
    xrange = range

VERSION='0.1'

class User(dict):
    """ name, date """
    def __init__(self, name):
        self['name'] = name
        self['date'] = time.time()

class Answers(list):
    """ user, quizz id, score, list choices """
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
    """ text, comment """
    def __init__(self, **kwargs):
        self.text = kwargs.get('text','')
        self.comment = kwargs.get('comment','')
        self.correct = kwargs.get('correct',False)
class Question(list):
    """ title, text, list of choices, index correct """
    def __init__(self, **kwargs):
        self.title = kwargs.get('title','')
        self.text =  kwargs.get('text','')
        self.correct = None
        for i,c in enumerate(kwargs.get('choices',[])):
            c = Choice(**c)
            self.append(c)
            if c.correct:
                assert self.correct == None, """
                    current implementation assumes there is only one
                    correct answer per question """
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

class PageData(dict):
    template = 'invalid.html'
    def __init__(self, info, **kwargs):
        self.info = info
        dict.__init__(self, **kwargs)
class PageConfirm(PageData):
    template = 'confirm.html'
class PageQuestion(PageData):
    template = 'question.html'
class PageScore(PageData):
    template = 'score.html'

class QuizzApp(dict):

    def __init__(self):
        self['auth'] = {}
        self['user'] = []
        self['assignment'] = []
        self['question'] = []
        self['quizz'] = []

    def number_of(self,db):
        assert db in self
        return len(self[db])

    def get(self, db, index):
        assert db in self and isinstance(self[db], list)
        assert index < len(self[db]), """ illegal index %i in table %s """ % (index, db)
        return self[db][index]

    def add(self, db, entry):
        assert db in self and isinstance(self[db], list)
        self[db].append(entry)
        return len(self[db]) - 1

    def new_user(self, name, auth):
        """ return index uid """
        assert auth not in self['auth'], "auth key %s already used"%auth
        uid = self.add('user', User(name))
        self['auth'][auth] = uid
        return uid

    def new_quizz(self,length=3,maxanswers=3):
        """ generates a random quizz, return index qid """
        quizz = Quizz()
        pool = self.number_of('question')
        for iq in random.sample(xrange(pool), length):
            q = self.get('question',iq)
            # choose some choices, the first one is correct
            assert q.correct == 0, """ implementation assumes correct answer comes first, here correct = %i in question %s """ % (q.correct, q.text)
            c = random.sample(xrange(1,len(q)), maxanswers - 1)
            c.append(0)
            random.shuffle(c)
            quizz.append( (iq, c) )

        return self.add('quizz',quizz)

    def new_assignment(self, uid, qid):
        """ return index aid of new assignment """
        quizz = self.get('quizz',qid)
        answers = Answers(uid, qid, quizz)
        return self.add('assignment',answers)

    def post_answer(self, info, choice):
        """ save answer and return index of next question """
        uid, aid, number = info
        answers = self.get('assignment',aid)
        assert number < len(answers), """ wrong number %i >= len(assignment) """ % number
        if answers.confirmed:
            return None
        answers.set_choice(number, choice)
        return PageData((uid,aid,number+1))

    def post_confirmation(self, info):
        """ mark assignment as done and return score """
        uid, aid = info
        #user,answers,question = self.parse_token(token)
        answers = self.get('assignment',aid)
        answers.confirmed = True
        return self.get_score_page(info)

    def get_question_page(self, info):
        """
        info contains uid, aid, number
        returns the question data,
        If number > number of questions,
        return confirmation page or score instead.
        """
        uid, aid, number = info
        #user = self.get('user',uid)
        answers = self.get('assignment',aid)
        quizz = self.get('quizz',answers.qid)

        if number >= len(answers):
            return self.get_score_page((uid,aid))

        qid, choices_index = quizz[number]
        question = self.get('question',qid)
        choices = [ question[c] for c in choices_index ]
        return PageQuestion(info,
                   question=question,
                   number = number,
                   choices=choices,
                   selected=answers[number],
                   disabled=answers.confirmed)

    def grade(self, info):
        uid, aid = info
        user = self.get('user',uid)
        answers = self.get('assignment',aid)
        quizz = self.get('quizz',answers.qid)
        score = 0
        for choice, (qid, cid) in zip(answers,quizz):
            if app.config['verbose']:
                app.logger.info("choice %i in question %s"%(choice,(qid,cid)))
            question = self.get('question',qid)
            score += question.grade(cid[choice])
        answers.set_score(score)

    def get_score_page(self, info):
        uid, aid = info
        user = self.get('user',uid)
        answers = self.get('assignment',aid)
        if not answers.confirmed:
            return PageConfirm(info, user=user, answers=answers)
        if answers.score == None:
            self.grade(info)
        results = {
                'info': info,
                'name': user['name'],
                'score': answers.score,
                'questions': len(answers)
                }
        return PageScore(info, user=user,
                         answers=answers,
                         results=results)

    def load_questions_yaml(self, filename):
        import yaml

        with open(filename, 'r') as stream:
            try:
                for q in yaml.load_all(stream,Loader=yaml.SafeLoader):
                    self.add('question',Question(**q))
            except yaml.YAMLError as e:
                app.logger.info(e)

#####################################################################
#
# Web server
#
#####################################################################

from flask import Flask, request, render_template, abort, redirect, url_for, send_file

from itsdangerous import (URLSafeTimedSerializer, Serializer, BadSignature, SignatureExpired, NoneAlgorithm)
quizz = QuizzApp()
app = Flask('quizz')
app.config['verbose'] = False
app.config['SECRET_KEY'] = '<random>'
app.config['allow_register'] = False
app.config['number_questions'] = 5
app.config['number_choices'] = 3
app.config['token_method'] = 'default'
app.config['expiration_time'] = 0
app.config['lang'] = 'fr'
METHOD='GET'

def get_serializer(salt=''):
    if app.config['token_method'] == None:
        return Serializer(app.config['SECRET_KEY'],salt=salt,signer=None)
    elif app.config['token_method'] == 'default':
        return URLSafeTimedSerializer(app.config['SECRET_KEY'],salt=salt)
    else:
        return URLSafeTimedSerializer(app.config['SECRET_KEY'],salt=salt)

@app.template_filter('token')
def tokenize(data, salt='quizz',expiration=600):
    """
    creates a token for the given data
    """
    s = get_serializer(salt)
    if app.config['verbose']:
        app.logger.info("tokenize %s"%(data,))
    return s.dumps(data)

@app.template_filter('url_protected')
def url_protected(route,data,**kwargs):
    token = tokenize(data,salt=route)
    return url_for(route,token=token,**kwargs)

def load_token(token, salt=''):
    s = get_serializer(salt)
    try:
        if app.config['verbose']:
            app.logger.info("parse token %s"%(token,))
        data = s.loads(token)
    except SignatureExpired:
        # FIXME: return expiration page
        if app.config['verbose']:
            app.logger.info("signature expired")
        return None # valid token, but expired
    except BadSignature:
        if app.config['verbose']:
            app.logger.info("bad signature")
        return None # invalid token
    if app.config['verbose']:
        app.logger.info("got %s"%(data,))
    return data

from functools import wraps
def token_required(f):
    """
    requires a valid token, whose salt
    is the name of the embedded function
    """
    @wraps(f)
    def decorated(*args,**kwargs):
        token = request.args.get('token',None)
        if token is None:
            return render_template("illegal.html"), 401
        if app.config['verbose']:
            app.logger.info("[page %s, read access token]"%f.__name__)
        data = load_token(token, salt = f.__name__)
        if data is None:
            app.logger.info('[INVALID TOKEN] %s'%(token,))
            return render_template("illegal.html"), 401
        try:
            return f(*args,data=data,**kwargs)
        except AssertionError:
            app.logger.info("[INVALID] not in the database")
            return render_template("illegal.html"), 401
        except TypeError:
            app.logger.info("[TYPE ERROR] wrong entry")
            return render_template("illegal.html"), 401
    return decorated

def render_page(data,route=None):
    if data is None:
        if app.config['verbose']:
            app.logger.info("[ILLEGAL] empty page")
        return render_template('illegal.html')
    if isinstance(data, PageData) and route is None:
        return render_template(data.template, this=data)
    elif route:
        if app.config['verbose']:
            app.logger.info("[CREATE TOKEN] for page %s using data %s"%(route,data.info))
        return redirect(url_protected(route, data.info))
    else:
        if app.config['verbose']:
            app.logger.info("[BUG] no route to render %s"%(data,))
        return render_template('illegal.html')

@app.route('/')
def index():
    return render_template('index.html',token_link=app.config['allow_register'])

@app.route('/token', methods = [METHOD])
@token_required
def api_token(data=None):
    """ generates valid tokens

    FIXME:
    right now this is open bar

    In the future this page must be protected
    and tokens generated by authorized people only.
    """
    auth = quizz.number_of('auth')
    return render_template('token.html',auth=auth)

@app.route('/activate', methods = [METHOD])
@token_required
def api_activate(data=None):
    return render_template('register.html', auth=data)

@app.route('/api/register', methods = [METHOD])
@token_required
def api_register(data=None):
    """ token data (registration key) """
    auth = str(data)
    name = unicode(request.args.get('name'))
    uid = quizz.new_user(name, auth)
    qid = quizz.new_quizz(app.config['number_questions'],
                          app.config['number_choices'])
    aid = quizz.new_assignment(uid, qid)
    if app.config['verbose']:
        app.logger.info("created user %i,quizz %i,assignment %i"%(uid,qid,aid))
    return render_page(PageData((uid,aid,0)), 'api_question')

@app.route('/question', methods = [METHOD])
@token_required
def api_question(data=None):
    """ token data (uid, aid, number) """
    page = quizz.get_question_page(data)
    return render_page(page)

@app.route('/score', methods = [METHOD])
@token_required
def api_score(data=None):
    """ token data (uid, aid, number) """
    page = quizz.get_score_page(data)
    return render_page(page)

@app.route('/results', methods = [METHOD])
@token_required
def api_view(data=None):
    """ token data (name, score, uid, aid) """
    return render_template("results.html", this=data)

@app.route('/api/answer', methods = [METHOD])
@token_required
def api_answer(data=None):
    """ token data (uid, aid, number) """
    choice = int(request.args.get('choice'))
    data = quizz.post_answer(data, choice)
    return render_page(data, 'api_question')

@app.route('/api/submit', methods = [METHOD])
@token_required
def api_submit(data=None):
    """ token data (uid, aid) """
    app.logger.info('received token %s' % data)
    data = quizz.post_confirmation(data)
    return render_page(data, 'api_score')

import pyqrcode
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

@app.route('/images/svg',methods = [METHOD])
@token_required
def api_svg(data=None):
    try:
        stream = StringIO()
        code = pyqrcode.create(data)
        code.svg(stream, scale=1)
        stream.seek(0)
        #if sys.version_info.major == 3:
        #    stream = io.BytesIO(stream.encode())
        return send_file(stream, mimetype='image/svg+xml')
    except e:
        return e
    return send_file(stream, mimetype='image/svg+xml', as_attachment=True)

#####################################################################
#
# Command line application
#
#####################################################################

import click

@click.group()
def cli():
    pass

@cli.command()
@click.option('--debug', default=False, is_flag=True, help='turn on Flask debug mode')
@click.option('--verbose', default=False, is_flag=True, help='log requests')
@click.option('--allow-register', default=False, is_flag=True, help='provide registration link at index page')
@click.option('--number_questions', default=5, help='number of questions per quizz')
@click.option('--number_choices', default=3, help='number of choices per question')
@click.option('--secret_key', default='lilalilalou', help='secret key')
@click.option('--token_method', type=click.Choice(['none', 'default']), default='default', help='token method')
def server(debug,
        verbose,
        allow_register,
        number_questions,
        number_choices,
        secret_key,
        token_method):
    app.config['verbose'] = verbose
    app.config['SECRET_KEY'] = secret_key
    app.config['allow_register'] = allow_register
    app.config['number_questions'] = number_questions
    app.config['number_choices'] = number_choices
    app.config['token_method'] = token_method
    app.run(debug=debug)

@cli.command()
@click.option('--yaml',default='questions.yaml',
        help='load questions file')
def build(yaml):
    pass

if __name__ == '__main__':
    quizz.load_questions_yaml('example.yaml')
    cli()
