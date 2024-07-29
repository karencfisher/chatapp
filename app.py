import atexit
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, make_response, redirect
from flask_login import login_user, current_user, logout_user, login_required,\
                  LoginManager, UserMixin

from Chat.chat import Chat
from Authentication.login import check_login, get_user, add_user, change_password


app = Flask(__name__)
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'home'  # Define the view for login page

################ authentication ###########################################

@login_manager.user_loader
def load_user(user_id):
    user = get_user(user_id)
    if user:
        return User(user)
    return None

class User(UserMixin):
    def __init__(self, args):
        self.id = args[0]
        self.username = args[1]
        self.password = args[2]
        self.admin = args[3]
        self.temp_pw = args[4]
        self.name = args[5]
        self.location = args[6]
    
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect('/chat')
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    result = check_login(username, password)
    if result is not None:
        login_user(User(result))
        return redirect('/chat')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

################ protected routes ###########################################

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
        name = current_user.name
        location = current_user.location
        dialog = llm.get_conversation(session_id, name, location)
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
    
@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user_form():
    if request.method == 'POST':
        if not current_user.admin:
            return jsonify({"error": "Access Denied"}), 403
        username = request.form['username']
        password = request.form['password']
        try:
            add_user(username, password)
        except ValueError:
            return jsonify({"error": "Username already in use"}), 400
        return jsonify({"success": "User added"}), 200

    else:
        if not current_user.admin:
            return "<h1 style=\"color: red;\">Access Denied</h1>", 403
        return render_template('add_user.html')
    
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_pw():
    if request.method == 'POST':
        new_password = request.form['new_password']
        change_password(current_user.id, new_password)
    else:
        return render_template('change_password.html')



def close_server():
    llm.close_server()

if __name__ == '__main__':
    llm = Chat()
    atexit.register(close_server)
    app.run(debug=True, host='0.0.0.0', port=5005)
