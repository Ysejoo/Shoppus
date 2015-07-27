# -*- coding : utf-8 -*-
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
import smtplib, email, random
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from test.test_typechecks import Integer

#configuration
DATABASE = "/tmp/shoppustest1.db"
PER_PAGE = 30
DEBUG = True
SECRET_KEY = "development key"

#create application
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar("shoppustest1_settings", silent=True)

#user checked configuration
# 0 : only register email
# 1 : checked email
# 2 : submit all information
# 5 : administrator

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

def get_user_email(uemail):
    rv = g.db.execute('select useremail from users where useremail = ?',
                     [uemail]).fetchone()
    return rv[0] if rv else None

def get_checkcode(checkcode):
    rv = g.db.execute('select code from checkcode where code = ?',
                      [checkcode]).fetchone()
    return rv[0] if rv else None


@app.before_request
def before_request():
    g.db = connect_db()
    g.user = None
    if 'uemail' in session:  
        g.user = query_db('select * from users where useremail = ?',
                          [session['uemail']], one=True)

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
        if not request.form['inputemail']:
            error = "YOU DIDINT INPUT EMAIL ADDRESS!"
        elif not request.form['inputpw']:
            error = "YOU DIDNT INPUT PASSWORD!"
        else:
            user = query_db(''' select * from users where useremail = ? ''', 
                        [request.form['inputemail']], one = True)
            if user is None:
                error = "The Email is not exist!"
            elif not check_password_hash(user['pw'], request.form['inputpw']):
                    error = "The Password is not correct!"
            elif user['checked'] == 0:
                return render_template("emailcheck.html", uemail = request.form['inputemail'])
            elif user['checked'] == 1:
                return render_template("registerinfo.html", uemail = request.form['inputemail'])
            else:
                session['uemail'] = user['useremail']
                return redirect(url_for('main'))
    return render_template("login.html", error = error)

@app.route("/logout")
def logout():
    session.pop('uemail', None)
    return redirect(url_for('main'))


@app.route("/emailregist", methods=['GET','POST'])
def emailregist():
    if g.user:
        return redirect(url_for('main'))
    error = None 
    if request.method == 'POST':
        if not request.form['inputemail']:
            error = "YOU DIDINT INPUT EMAIL ADDRESS!"
        elif not request.form['inputpw']:
            error = "YOU DIDNT INPUT PASSWORD!"
        elif not '@' in request.form['inputemail']:
            error = "WORNG EMAIL ADDRESS!"
        elif get_user_email(request.form['inputemail']) is not None:
                error = "THIS EMAIL IS ALREADY TAKEN!"
        else:
            g.db.execute('''insert into users (useremail, pw, checked, userdate) values(?, ?, ?, ?)''',
                         [request.form['inputemail'], 
                          generate_password_hash(request.form['inputpw']), 
                          0, 
                          time.strftime('%Y-%m-%d')])
            g.db.commit()
            return render_template("emailcheck.html", uemail = request.form['inputemail'])
    return render_template("emailregist.html", error=error)

@app.route("/sendemail/<addr>")
def sendemail(addr):
    randomcode = random.uniform(100000, 999999)
    newcode = str(int(randomcode))
    
    g.db.execute('''insert into checkcode (code) values (?)''', [newcode])
    g.db.commit()
    
    host = "smtp.gmail.com"
    port = 587
    text = "[Shoppus] your code is : "+ newcode
    senderAddr = "nassune@gmail.com"
    senderpw = "dbs0412."
    recipientAddr = addr
    
    msg = MIMEText(text)
    msg['Subject'] = "Shoppus Email Sender"
    msg['From'] = senderAddr
    msg['To'] = recipientAddr
    
    s=smtplib.SMTP(host, port)
    s.set_debuglevel(1)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(senderAddr, senderpw)
    s.sendmail(senderAddr,[recipientAddr], msg.as_string())
    s.close()
    mssg = "The code is sended"
    return render_template("emailcheck.html", uemail = addr, mssg = mssg)

@app.route("/emailcheck/<addr>", methods=['GET','POST'])
def emailcheck(addr):
    if g.user:
        return redirect(url_for('main'))
    error = None
    mssg = "The code is sended"
    if request.method=='POST':
        if not request.form['inputcode']:
            error = "Code is not Inputed!"
        elif get_checkcode(request.form['inputcode']) is None:
            error = "Wrong Code!"
        else:
            g.db.execute('''update users set checked = 1 where useremail = ? ''',[addr])
            g.db.commit()
            g.db.execute('''delete from checkcode where code = ?''',[request.form['inputcode']])
            g.db.commit()
            return render_template("registerinfo.html", uemail = addr) 
    return render_template("emailcheck.html", error = error, uemail = addr, mssg = mssg)

@app.route("/registerinfo/<addr>", methods=['GET', 'POST'])
def registerinfo(addr):
    if g.user:
        return redirect(url_for('main'))
    error = None
    if request.method == 'POST':
        if not request.form['inputnickname']:
            error = "You didn't input the Nickname"
        else:
            g.db.execute('''update users set checked = 2, nick = ?, birth = ?, sex = ? where useremail = ?''',
                         [request.form['inputnickname'], request.form['inputbirth'], request.form['inputgender'], addr])
            g.db.commit()
            return render_template("login.html", nowemail=addr, registsuccess = "Regist Complete!")            
    return render_template("registerinfo.html", error=error, uemail=addr)

@app.route("/registermoreinfo/<addr>", methods=['GET', 'POST'])
def registermoreinfo(addr):
    if addr:
        return redirect(url_for('main'))
    else:
        return redirect(url_for('main')) 


@app.route("/minitwit", methods=['GET', 'POST'])
def minitwit():
    if not g.user:
        return redirect(url_for('main'))
    twits = query_db('''select * from wallpaper natural join users order by wdate desc''')
    comments = query_db('''select * from wallcomment natural join users''')
    undercomments = query_db('''select * from commentcomment natural join users''')
    return render_template("minitwit.html", twits = twits, 
                                            comments = comments, 
                                            cc = undercomments,)
    
# BLOCK TEST============================================================================
@app.route("/minitwittest", methods=['GET', 'POST'])
def test_minitwit():
    if not g.user:
        return redirect(url_for('main'))
    twits = query_db('''select * from wallpaper''')
    comments = query_db('''select * from wallcomment''')
    return render_template("test_minitwit.html", twits = twits, comments = comments)

@app.route("/getwallpapertest/<idx>")
def test_getcomment(idx):
    if not g.user:
        return redirect(url_for('main'))
    if idx:
        return render_template("test_minitwit_wallcomment.html", 
                               tt = query_db('''select * from wallcomment where wallidx = ? ''', 
                                             [idx]))
    return render_template("test_minitwit_wallcomment.html", tt=None)
# END TEST============================================================================

@app.route("/minitwit/addtwit/<addr>", methods=['GET', 'POST'])
def addtwit(addr):
    if not g.user:
        return redirect(url_for('main'))
    if request.method == 'POST':
        error = None
        if not request.form['inputtwit']:
            error = "You didn't insert messages"
            twits = query_db('''select * from wallpaper natural join users order by wdate desc''')
            comments = query_db('''select * from wallcomment natural join users''')
            undercomments = query_db('''select * from commentcomment natural join users''')
            return render_template("minitwit.html", twits = twits, 
                                                    comments = comments, 
                                                    cc = undercomments, 
                                                    error=error)
        elif request.form['inputtwit'] == "What's on your mind?":
            error = "You didn't insert messages"
            twits = query_db('''select * from wallpaper natural join users order by wdate desc''')
            comments = query_db('''select * from wallcomment natural join users''')
            undercomments = query_db('''select * from commentcomment natural join users''')
            return render_template("minitwit.html", twits = twits, 
                                                    comments = comments, 
                                                    cc = undercomments, 
                                                    error=error)
            return render_template("minitwit.html", twits = query_db('''
                            select * from wallpaper natural join users'''), error=error)            
        else:
            g.db.execute(''' insert into wallpaper (useremail, wcontent, wlike, wdate, wtime) values (?,?,?,?,?) ''',
                         [addr, request.form['inputtwit'], 0, time.strftime('%Y-%m-%d %H:%M:%S'), int(time.time())])
            g.db.commit()
            return redirect(url_for('minitwit'))
        return redirect(url_for('main'))

@app.route("/minitwit/deletetwit/<idx>")
def deletetwit(idx):
    if not g.user:
        return redirect(url_for('main'))    
    if idx:
        g.db.execute(''' delete from wallpaper where wallidx =  ?''', [idx])
        g.db.commit()
        g.db.execute(''' delete from wallcomment where wallidx = ?''',[idx])
        g.db.commit()
        g.db.execute(''' delete from commentcomment where wallidx = ?''',[idx])
        g.db.commit()
    return redirect(url_for('minitwit'))

@app.route("/minitwit/twitpluslike/<idx>/<int:clike>/<addr>")
def twitpluslike(idx, clike, addr):
    if not g.user:
        return redirect(url_for('main'))
    if idx and addr:
        likes = query_db('''select * from userlikeWP where wallidx = ? and useremail = ?''',
                         [idx, addr])
        if likes:
            flash('You already liked this~!')
            return redirect(url_for('minitwit'))
        else:
            g.db.execute(''' update wallpaper set wlike = ? where wallidx = ? ''', 
                         [clike+1 ,idx])
            g.db.commit()
            g.db.execute(''' insert into userlikeWP (wallidx, useremail) values(?, ?)''', 
                         [idx, addr])
            g.db.commit()
    return redirect(url_for('minitwit'))

@app.route("/minitwit/twitaddcomment/<int:idx>/<addr>", methods=['GET', 'POST'])
def twitaddcomment(idx, addr):
    if not g.user:
        return redirect(url_for('main'))
    if request.method == 'POST':
        if idx:
            if request.form['inputcomment']:
                g.db.execute(''' insert into wallcomment (wallidx, useremail, ccontent, clike, cdate, ctime) values(?,?,?,?,?,?)''',
                             [idx, addr, request.form['inputcomment'], 0, time.strftime('%Y-%m-%d %H:%M:%S'), int(time.time())])
                g.db.commit()
    return redirect(url_for('minitwit'))

@app.route("/minitwit/commentpluslike/<cidx>/<int:clike>/<addr>")
def commentpluslike(cidx, clike, addr):
    if not g.user:
        return redirect(url_for('main'))
    if cidx and addr:
        likes = query_db('''select * from userlikeWC where commentidx = ? and useremail = ?''',
                         [cidx, addr])
        if likes:
            flash('You already liked this~!')
            return redirect(url_for('minitwit'))        
        else:
            g.db.execute(''' update wallcomment set clike = ? where commentidx = ? ''',
                         [clike+1, cidx])
            g.db.commit()
            g.db.execute(''' insert into userlikeWC (commentidx, useremail) values(?, ?)''', 
                         [cidx, addr])
            g.db.commit()
    return redirect(url_for('minitwit'))

@app.route("/minitwit/commentdelete/<cidx>")
def commentdelete(cidx):
    if not g.user:
        return redirect(url_for('main'))
    if cidx:
        g.db.execute(''' delete from wallcomment where commentidx = ?''', [cidx])
        g.db.commit()
        g.db.execute(''' delete from commentcomment where commentidx = ?''',[cidx])
        g.db.commit()
    return redirect(url_for('minitwit'))

@app.route("/minitwit/commentaddcomment/<idx>/<cidx>/<addr>", methods=['GET', 'POST'])
def commentaddcomment(idx, cidx, addr):
    if not g.user:
        return redirect(url_for('main'))
    if request.method == "POST":
        if idx and cidx and addr:
            g.db.execute(''' insert into commentcomment (wallidx, commentidx, useremail, cccontent, cclike, ccdate, cctime) values (?,?,?,?,?,?,?)''',
                         [idx, cidx, addr, request.form['inputcommentreply'], 0, time.strftime('%Y-%m-%d %H:%M:%S'), int(time.time())])
            g.db.commit()
    return redirect(url_for('minitwit'))

@app.route("/minitwit/commentcommentpluslike/<ccidx>/<int:cclike>/<addr>")
def commentcommentpluslike(ccidx, cclike, addr):
    if not g.user:
        return redirect(url_for('main'))
    if ccidx and addr:
        likes = query_db('''select * from userlikeCC where ccommentidx = ? and useremail = ?''',
                         [ccidx, addr])
        if likes:
            flash('You!!!!')
            return redirect(url_for('minitwit'))
        else:
            g.db.execute(''' update commentcomment set cclike = ? where ccommentidx = ? ''',
                        [cclike+1, ccidx])
            g.db.commit()
            g.db.execute(''' insert into userlikeCC (ccommentidx, useremail) values(?, ?)''', 
                         [ccidx, addr])
            g.db.commit()            
    return redirect(url_for('minitwit'))

@app.route("/minitwit/commentcommentdelete/<ccidx>")
def commentcommentdelete(ccidx):
    if not g.user:
        return redirect(url_for('main'))
    if ccidx:
        g.db.execute(''' delete from commentcomment where ccommentidx = ? ''',[ccidx])
        g.db.commit()
    return redirect(url_for('minitwit'))

# additional functions
@app.route("/members")
def showmember():
    return render_template('blocks.html', members = query_db('''
    select * from users'''))
    
@app.route("/codes")
def showcheckcodes():
    return render_template("checkcodes.html", codes = query_db('''
    select * from checkcode'''))

@app.route("/deletemember/<thisemail>", methods=['GET', 'POST'])
def deletemember(thisemail):
    if request.method == 'POST':
        g.db.execute(''' delete from users where useremail = ? ''', [thisemail])
        g.db.commit()
    return redirect(url_for('showmember'))

@app.route("/testpage")
def testpage():
    nowdate = int(time.time())
    return render_template("testpage.html", d = nowdate)




@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

if __name__ == "__main__":
    init_db()
    app.run()
