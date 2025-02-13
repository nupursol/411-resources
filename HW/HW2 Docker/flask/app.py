from flask import Flask, make_response
import os

app = Flask(__name__)

@app.route('/')
def hello():
    response = make_response(
        {
            'response': 'Hello, World!',
            'status': 200
        }
    )
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT', default=None), debug=True)
