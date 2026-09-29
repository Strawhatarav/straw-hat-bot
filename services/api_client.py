import asyncio
import logging
import time
from collections import OrderedDict

import aiohttp

log = logging.getLogger(__name__)


class APIError(Exception):
    """A safe, user-facing API failure."""


class TTLCache:
    def __init__(self, ttl=300, maxsize=256):
        self.ttl = ttl
        self.maxsize = maxsize
        self._items = OrderedDict()

    def get(self, key):
        item = self._items.get(key)
        if not item:
            return None
        expires, value = item
        if expires <= time.monotonic():
            self._items.pop(key, None)
            return None
        self._items.move_to_end(key)
        return value

    def set(self, key, value):
        self._items[key] = (time.monotonic() + self.ttl, value)
        self._items.move_to_end(key)
        while len(self._items) > self.maxsize:
            self._items.popitem(last=False)


class APIClient:
    def __init__(self):
        self.session = None
        self.cache = TTLCache()

    async def start(self):
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=12, connect=5)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": "StrawHatBot/1.0 (Discord community bot)"}
            )

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_json(self, url, *, params=None, headers=None, cache_ttl=300):
        await self.start()
        cache_key = (url, tuple(sorted((params or {}).items())))
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        for attempt in range(2):
            try:
                async with self.session.get(url, params=params, headers=headers) as response:
                    if response.status == 429:
                        retry = response.headers.get("Retry-After", "2")
                        if attempt == 0:
                            try:
                                await asyncio.sleep(min(float(retry), 5))
                                continue
                            except ValueError:
                                pass
                        raise APIError("The service is receiving too many requests. Please try again shortly.")
                    if response.status in (401, 403):
                        raise APIError("The API key is missing, invalid, or not permitted.")
                    if response.status == 404:
                        raise APIError("No matching result was found.")
                    if response.status >= 500:
                        raise APIError("The external service is temporarily unavailable.")
                    if response.status >= 400:
                        raise APIError(f"The external service returned an error (HTTP {response.status}).")
                    data = await response.json(content_type=None)
                    self.cache.set(cache_key, data)
                    return data
            except asyncio.TimeoutError:
                raise APIError("The request timed out. Please try again.")
            except aiohttp.ClientError as exc:
                log.warning("External API request failed: %s", exc)
                raise APIError("I couldn't reach the external service. Please try again.")
        raise APIError("The external service is temporarily unavailable.")
