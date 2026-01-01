from flask import Flask, request, Response
import json
from rate_limiter import RateLimiter

app = Flask(__name__)
rate_limiter = RateLimiter()

@app.route("/test")
def test():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    result = rate_limiter.limit_request(ip)

    if isinstance(result, tuple):
        data, status = result
    else:
        data, status = result, 200

    body = json.dumps(data, ensure_ascii=False)
    return Response(body, status=status, content_type="application/json; charset=utf-8")

@app.route("/test/view")
def test_view():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    result = rate_limiter.limit_request(ip)

    if isinstance(result, tuple):
        data, status = result
    else:
        data, status = result, 200

    pretty = json.dumps(data, ensure_ascii=False, indent=2)
    return Response(f"<pre>{pretty}</pre>", status=status, content_type="text/html; charset=utf-8")
