import atexit
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, make_response,\
                  session, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required

from Chat.chat import Chat
from Authentication.login import User, LoginForm


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Authentication/users.sqlite'
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db = SQLAlchemy(app)


@app.route('/')
def home():
    # if session['logged_in']:
    #     return redirect(url_for('/chat'))
    return render_template('login.html', form=LoginForm())

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    user = User.query.filter_by(username=form.username.data).first()
    if user and user.check_password(form.password.data):
        session['logged_in'] = True
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/chat')
@login_required
def chat():
    response = make_response(render_template('chatbot.html', model=llm.getModel()))
    if request.cookies.get('chatsession') is None:
        response.set_cookie('chatsession', os.urandom(24).hex())
    return response

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    try:
        session_id = request.cookies.get('chatsession')
        data = request.get_json()
        message = data.get('message')
        response = llm.chat(session_id, message)
        return jsonify({"message": response}), 200
    except Exception as ex:
        return jsonify({"Error": str(ex)})

@app.route('/conversation')
@login_required
def conversation():
    try:
        session_id = request.cookies.get('chatsession')
        dialog = llm.get_conversation(session_id)
        return jsonify(dialog), 200
    except Exception as ex:
        return jsonify({"Error": str(ex)})

@app.route('/clear_session')
@login_required
def close_session():
    try:
        session_id = request.cookies.get('chatsession')
        llm.clear_session(session_id)
        return jsonify({"success": "cleared session"}), 200
    except Exception as ex:
        return jsonify({"Error": str(ex)})

def close_server():
    llm.close_server()

if __name__ == '__main__':
    llm = Chat()
    atexit.register(close_server)
    app.run(debug=True, host='0.0.0.0', port=5005)
