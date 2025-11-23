import os

import redis


class Redis:
    def __init__(self):
        self.redis = redis.Redis(
            connection_pool=redis.ConnectionPool(
                host=os.environ.get('REDIS_HOST'),
                port=os.environ.get('REDIS_PORT'),
                password=os.environ.get('REDIS_PASSWORD'),
                db=os.environ.get('REDIS_DB'),
                decode_responses=True
            )
        )

    def set(self, key: str, value: str, expire_time=0):
        self.redis.set(key, value, ex=expire_time)

    def get(self, key):
        return self.redis.get(key)

    def delete(self, key):
        return self.redis.delete(key)
