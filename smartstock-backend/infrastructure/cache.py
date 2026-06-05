import json
import redis as redis_lib


class RedisCache:
    def __init__(self):
        self.client = redis_lib.Redis.from_url('redis://localhost:6379/0')

    def get(self, key: str):
        value = self.client.get(key)
        return json.loads(value) if value else None

    def set(self, key: str, value, ttl: int = 300):
        self.client.setex(key, ttl, json.dumps(value))

    def delete(self, key: str):
        self.client.delete(key)
