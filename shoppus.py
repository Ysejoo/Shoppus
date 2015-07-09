'''
Created on 2015. 7. 7.

@author: Yoon Se Joo

'''

from __future__ import with_statement
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
import time
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash
from werkzeug.security import check_password_hash, generate_password_hash
from pip._vendor.distlib._backport.tarfile import TUREAD


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


@app.before_request
def before_request():
    g.db = connect_db()
    g.user = None
    if 'mid' in session:
        g.user = query_db('select * from user where mid = ?',
                          [session['mid']], one=True)


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()





@app.route("/")
def main():
    return render_template("blocks.html")

@app.route("/register", methods=['GET', 'POST'])
def goregister():
    return render_template("register.html")





if __name__ == "__main__":
    init_db()
    app.run()
