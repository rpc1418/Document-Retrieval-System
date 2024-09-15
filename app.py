print("jai shree ganesh")
from flask import Flask

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return {'status': 'API is active'}, 200

if __name__ == '__main__':
    app.run(debug=True)
