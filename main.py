# main.py
from flask_cors import CORS
from flask import send_from_directory
from app import create_app
import os

app = create_app()
CORS(app)

# === 关键部分：让 Flask 正确返回 UI 文件夹下的页面 ===
@app.route('/')
def serve_index():
    return send_from_directory(os.path.join(os.getcwd(), 'UI'), 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(os.path.join(os.getcwd(), 'UI'), path)

# ========================================================

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
