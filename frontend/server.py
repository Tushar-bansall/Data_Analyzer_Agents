# server.py
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')

FRONTEND_DIR = Path(__file__).parent

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    # serve app.js, favicon.ico, css etc.
    return send_from_directory(FRONTEND_DIR, filename)

@app.route('/analyze', methods=['POST'])
def analyze():
    # example: accept JSON or form data
    data = request.get_json(silent=True) or request.form.to_dict()
    # do whatever analysis you need here
    result = {"status": "ok", "received": data}
    return jsonify(result)

if __name__ == "__main__":
    # run on port 3000
    app.run(host="0.0.0.0", port=3000, debug=True)
