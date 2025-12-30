from flask import Flask, request, jsonify
from collections import defaultdict
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

app.json.ensure_ascii = False

KST = timezone(timedelta(hours=9))

TIME_WINDOW_SECONDS = 60   
MAX_REQUESTS = 10         

request_history = defaultdict(list)

@app.route("/test")
def test():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    now = datetime.now(KST)

    request_history[ip] = [
        t for t in request_history[ip]
        if (now - t).total_seconds() <= TIME_WINDOW_SECONDS
    ]

    if len(request_history[ip]) >= MAX_REQUESTS:
        oldest_request = request_history[ip][0]

        retry_after = max(
            0,
            TIME_WINDOW_SECONDS - int((now - oldest_request).total_seconds())
        )

        response = jsonify({
            "error": "Too Many Requests",
            "message": "요청 횟수 제한을 초과했습니다.",
            "retry_after_seconds": retry_after
        })

        response.headers["Retry-After"] = retry_after

        return response, 429

    # 요청 허용 → 현재 시간 기록
    request_history[ip].append(now)

    return jsonify({
        "message": "request accepted",
        "ip": ip,
        "request_count": len(request_history[ip]),
        "timestamps": [
            t.strftime("%Y-%m-%d %H:%M:%S")
            for t in request_history[ip]
        ]
    })

if __name__ == "__main__":
    app.run(debug=True)