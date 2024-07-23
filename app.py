import atexit
from flask import Flask, jsonify, request, render_template
from chat import Chat


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('chatbot.html', 
                           model=llm.getModel())

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    message = data.get('message')
    response = llm.chat(message)
    return jsonify({"message": response})

@app.route('/conversation')
def conversation():
    dialog = llm.get_conversation()
    return jsonify(dialog), 200

def closeServer():
    llm.closeServer()

if __name__ == '__main__':
    llm = Chat()
    atexit.register(closeServer)
    app.run(debug=True, host='0.0.0.0', port=5005)
