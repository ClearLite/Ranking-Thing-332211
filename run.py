# run.py
import os
import socket
import subprocess
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder="dist", static_url_path="")

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_files(path):
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"Starting Series Graph Clone on http://{local_ip}:5173")

    # Start the React dev server (Vite)
    try:
        subprocess.Popen(["npm", "run", "dev"])
    except FileNotFoundError:
        print("❌ Please install dependencies with `npm install` first.")
    
    app.run(host="0.0.0.0", port=5173)
