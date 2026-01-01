import redis
from redis import ConnectionPool
from datetime import datetime, timezone, timedelta
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, TIME_WINDOW_SECONDS, MAX_REQUESTS

KST = timezone(timedelta(hours=9))

class RateLimiter:
    def __init__(self):
        pool = ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        self.r = redis.StrictRedis(connection_pool=pool)

    def limit_request(self, ip):
        now = datetime.now(KST).timestamp()
        key = f"request_history:{ip}"

        request_history = self.r.lrange(key, 0, -1)
        request_history = [float(t.decode()) for t in request_history]
        request_history = [t for t in request_history if (now - t) <= TIME_WINDOW_SECONDS]

        if len(request_history) >= MAX_REQUESTS:
            oldest_request = request_history[0]
            retry_after = TIME_WINDOW_SECONDS - int((now - oldest_request))
            return {
                "error": "Too Many Requests",
                "message": "요청 횟수 제한을 초과했습니다.",
                "retry_after_seconds": retry_after
            }, 429

        updated_history = request_history + [now]
        pipe = self.r.pipeline()
        pipe.delete(key)
        pipe.rpush(key, *updated_history)
        pipe.expire(key, TIME_WINDOW_SECONDS + 5)
        pipe.execute()

        return {
            "message": "request accepted",
            "ip": ip,
            "request_count": len(updated_history),
            "timestamps": [str(datetime.fromtimestamp(t, KST)) for t in updated_history]
        }
