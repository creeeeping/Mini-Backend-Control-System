from flask import Flask, request, jsonify
from collections import defaultdict
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# 한글 처리 설정 (ensure_ascii=False)
app.json.ensure_ascii = False

KST = timezone(timedelta(hours=9))

TIME_WINDOW_SECONDS = 60   
MAX_REQUESTS = 10         

# 요청 기록을 메모리에 저장하는 전역 변수
request_history = defaultdict(list)

@app.route("/test")
def test():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    now = datetime.now(KST)

    # 60초 이전 요청 제거 (Sliding Window)
    request_history[ip] = [
        t for t in request_history[ip]
        if (now - t).total_seconds() <= TIME_WINDOW_SECONDS
    ]

    # 요청 제한 초과 시 차단
    if len(request_history[ip]) >= MAX_REQUESTS:
        oldest_request = request_history[ip][0]

        retry_after = max(
            0,
            TIME_WINDOW_SECONDS - int((now - oldest_request).total_seconds())
        )

        # 응답 내용과 함께 Retry-After 헤더 추가
        response = jsonify({
            "error": "Too Many Requests",
            "message": "요청 횟수 제한을 초과했습니다.",
            "retry_after_seconds": retry_after
        })
        
        # 명시적으로 UTF-8 인코딩을 설정
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["Retry-After"] = retry_after

        return response, 429

    # 요청 허용 → 현재 시간 기록
    request_history[ip].append(now)

    # 요청 성공 응답
    response = jsonify({
        "message": "request accepted",
        "ip": ip,
        "request_count": len(request_history[ip]),
        "timestamps": [
            t.strftime("%Y-%m-%d %H:%M:%S")
            for t in request_history[ip]
        ]
    })

    # 명시적으로 UTF-8 인코딩을 설정
    response.headers["Content-Type"] = "application/json; charset=utf-8"

    return response

if __name__ == "__main__":
    app.run(debug=True)


# 한계 및 개선 사항

# 1. **전역 변수 문제**
#   현재 'request_history'는 전역 변수로 사용되고 있습니다. 
#   이는 모든 요청에 대해 서버의 메모리에 계속해서 데이터를 저장하게 되며, 
#   서버가 재시작되거나 종료될 때 데이터가 사라집니다. 또한, 요청이 많아지면 
#   메모리 사용량이 급격히 증가할 수 있습니다.
#   해결 방법: Redis와 같은 외부 캐시 시스템을 사용하여 데이터를 저장하고, 서버 재시작 시에도 데이터를 유지할 수 있도록 개선할 수 있습니다.

# 2. **메모리 관리**
#   서버의 메모리에 모든 요청 데이터를 저장하므로, 서버의 메모리가 부족해질 수 있습니다. 특히, 많은 사용자 요청을 처리하는 경우 메모리 사용량이 급증할 수 있습니다.
#   해결 방법: 데이터가 너무 많아지면 오래된 데이터를 자동으로 삭제하거나 외부 DB(예: Redis, MongoDB)에 데이터를 저장하는 방식으로 메모리 문제를 해결할 수 있습니다.

# 3. **확장성 문제**
#   이 코드는 단일 서버에서 동작하며, 서버를 수평 확장할 때 문제를 일으킬 수 있습니다. 여러 서버에서 동일한 요청 기록을 공유할 수 없기 때문입니다. 
#   해결 방법: 데이터의 일관성을 유지하려면 분산 캐시 시스템(예: Redis)이나 데이터베이스를 활용하여 여러 서버 간 데이터를 공유할 수 있도록 해야 합니다.

# 4. **확장성 및 유지 보수성 개선**
#   현재 코드 구조는 단일 기능을 처리하는 데 집중되어 있으므로, 더 많은 기능(예: API Key 기반 Rate Limiting)을 추가할 때 코드가 비대해질 수 있습니다.
#   해결 방법: 각 기능을 모듈화하여 여러 엔드포인트에서 관리할 수 있도록 구조를 개선해야 합니다. 예를 들어, Rate Limiter를 별도의 서비스나 미들웨어로 분리할 수 있습니다.

# 5. **부하 분산**
#   현재의 방식은 서버 부하가 증가할 경우 성능 저하가 발생할 수 있습니다. 여러 서버가 동일한 데이터를 처리하려면 부하 분산 및 세션 공유가 필요합니다.
#   해결 방법: 여러 서버가 같은 세션 정보를 공유할 수 있도록 외부 세션 스토리지(예: Redis)를 사용해야 합니다.
