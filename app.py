import atexit
import os
from flask import Flask, jsonify, request, render_template, make_response
from chat import Chat


app = Flask(__name__)

@app.route('/')
def home():
    response = make_response(render_template('chatbot.html', model=llm.getModel()))
    if request.cookies.get('chatsession') is None:
        response.set_cookie('chatsession', os.urandom(24).hex())
    return response

@app.route('/ask', methods=['POST'])
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
def conversation():
    try:
        session_id = request.cookies.get('chatsession')
        dialog = llm.get_conversation(session_id)
        return jsonify(dialog), 200
    except Exception as ex:
        return jsonify({"Error": str(ex)})

@app.route('/close_session')
def close_session():
    try:
        session_id = request.cookies.get('chatsession')
        llm.removeSession(session_id)
        return jsonify({"success": "closed session"}), 200
    except Exception as ex:
        return jsonify({"Error": str(ex)})

def closeServer():
    llm.closeServer()

if __name__ == '__main__':
    llm = Chat()
    atexit.register(closeServer)
    app.run(debug=True, host='0.0.0.0', port=5005)
