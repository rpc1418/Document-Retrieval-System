print("jai shree ganesh")
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return {'status': 'API is active'}, 200


# Placeholder for search logic
def perform_search(text, top_k, threshold):
    return [{"result": f"Result {i+1}"} for i in range(top_k)]

@app.route('/search', methods=['GET'])
def search():
    user_id = request.args.get('user_id')
    text = request.args.get('text', '')
    top_k = int(request.args.get('top_k', 10))
    threshold = float(request.args.get('threshold', 0.5))

    # Perform the search operation
    results = perform_search(text, top_k, threshold)
    
    return jsonify({"results": results}), 200

if __name__ == '__main__':
    app.run(debug=True)
