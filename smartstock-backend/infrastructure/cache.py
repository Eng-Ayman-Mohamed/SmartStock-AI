from django.core.cache import cache as django_cache


class RedisCache:
    def get(self, key: str):
        return django_cache.get(key)

    def set(self, key: str, value, ttl: int = 300):
        django_cache.set(key, value, timeout=ttl)

    def delete(self, key: str):
        django_cache.delete(key)

    def get_or_set(self, key: str, callable, ttl: int = 300):
        return django_cache.get_or_set(key, callable, timeout=ttl)
