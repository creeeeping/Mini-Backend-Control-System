from flask import Flask, request, jsonify
from collections import defaultdict
import time

app = Flask(__name__)

# IP별 요청 카운트 저장
request_count = defaultdict(int)

@app.route("/test")
def test():
    ip = request.remote_addr
    request_count[ip] += 1

    return jsonify({
        "message": "request received",
        "ip": ip,
        "count": request_count[ip],
        "timestamp": time.time()
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
