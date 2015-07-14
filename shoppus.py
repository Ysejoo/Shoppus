'''
Created on 2015. 7. 7.

@author: Yoon Se Joo

'''

from __future__ import with_statement
import time
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from contextlib import closing
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash
from werkzeug.security import check_password_hash, generate_password_hash



#configuration
DATABASE = "/tmp/shoppustest1.db"
PER_PAGE = 30
DEBUG = True
SECRET_KEY = "development key"

#create application
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar("shoppustest1_settings", silent=True)


def connect_db():
    """connect to database (shoppustest1.db)"""
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    """Creates the database tables."""
    with closing(connect_db()) as db:
        with app.open_resource('shoppustest1.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        
def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

def get_user_id(userid):
    rv = g.db.execute('select mid from member where mid = ?',
                     [userid]).fetchone()
                     
    return rv[0] if rv else None


@app.before_request
def before_request():
    g.db = connect_db()
    g.user = None
    if 'id' in session:  
        g.user = query_db('select * from member where mid = ?',
                          [session['id']], one=True)

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()





@app.route("/")
def main():
    return render_template("blocks.html")

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('main'))
    error = None
    if request.method == 'POST':
        user = query_db(''' select * from member where mid = ? ''', 
                        [request.form['iid']], one = True)
        if user is None:
            error = "The ID is not exist"
        elif user['mpw'] != request.form['ipw']:
            error = "The PW is not correct"
        else:
            session['id'] = user['mid']
            return redirect(url_for('main'))
    return render_template("logininfo.html", error = error)

@app.route("/logout")
def logout():
    session.pop('id', None)
    return redirect(url_for('main'))



@app.route("/register", methods=['GET', 'POST'])
def goregister():
    if g.user:
        return redirect(url_for('main'))
    error = None
    if request.method == 'POST':
        if not request.form['registerid']:
            error = "YOU DIDN'T INPUT THE ID"
        elif not request.form['registerpw']:
            error = "YOU DID'T INPUT THE PW"
        elif request.form['registerpw'] != request.form['registerpwRe']:
            error = "THE TWO PW IS NOT CORRECT!"
        elif get_user_id(request.form['registerid']) is not None:
            error = "THE ID IS ALREADY TAKEN"
        else:
            g.db.execute('''insert into member (mid, mpw) values(?,?)''',
                         [request.form['registerid'], request.form['registerpw']])
            g.db.commit()
            flash("YOU were succesfully registered and can login now!")
            return redirect(url_for('main'))
    return render_template("register.html", error=error)

@app.route("/members")
def showmember():
    return render_template('blocks.html', members = query_db('''
    select * from member'''))

@app.route("/deletemember", methods=['POST'])
def deletemember():
    if request.form['deletethis']:
        g.db.execute(''' delete from member where mid=?''', [request.form['deletethis']])
    return render_template('blocks.html')

if __name__ == "__main__":
    init_db()
    app.run()
