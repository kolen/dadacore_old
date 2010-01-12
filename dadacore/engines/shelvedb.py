from shelve import open as shelve_open
from time import time
from keyvalue import KeyValueModel

class ShelveProxyCachedValue:
    def __init__(self, value, dirty=False):
        self.lastaccess = time()
        self.value = value
        self.dirty = dirty
        self.hits = 0

    def _touch(self):
        """Update last access time and hits"""
        self.lastaccess = time()
        self.hits += 1

    def set(self, value):
        self.value = value
        self.dirty = True
        self._touch()

    def get(self):
        self._touch()
        return self.value

class ShelveProxy:
    """
    Proxy for Shelve hash-like object. Caches items.
    """

    _CACHE_KEYS = 50
    _CACHE_KEYS_CLEAN_THRESHOLD = 60
    _CACHE_ADD_SECONDS_FOR_EACH_HIT = 30

    def __init__(self, *pargs, **kwargs):
        """
        Creates ShelveProxy object, passing constructor arguments to shelve.open
        """
        self._s = shelve_open(*pargs, **kwargs)
        self._cache = {}

    def _cleanupIfThreshold(self):
        if len(self._cache) >= self._CACHE_KEYS_CLEAN_THRESHOLD:
            self._cleanup()

    def _cleanup(self):
        items = self._cache.items()
        items.sort(key=lambda x:
                       x[1].lastaccess +
                       x[1].hits * self._CACHE_ADD_SECONDS_FOR_EACH_HIT,
                   reverse=True)
        self._writeDirty(items[self._CACHE_KEYS:], delete=True)

    def _writeDirty(self, items, delete=False):
        for item in items:
            valueobj = self._cache[item[0]]
            if valueobj.dirty:
                self._s[item[0]] = valueobj.get()
            if delete:
                del self._cache[item[0]]
            else:
                self._cache[item[0]].dirty = False

    def __getitem__(self, key):
        if key in self._cache:
            value = self._cache[key].get()
        else:
            value = self._s[key]
            self._cache[key] = ShelveProxyCachedValue(value)

        self._cleanupIfThreshold()
        return value

    def __setitem__(self, key, value):
        self._cache[key] = ShelveProxyCachedValue(value, dirty=True)
        self._cleanupIfThreshold()

    def has_key(self, key):
        return self._cache.has_key(key) or self._s.has_key(key)

    def sync(self):
        self._writeDirty(self._cache.items())

    def __del__(self):
        self.sync()

class ShelveModel(KeyValueModel):

    DEFAULT_FILENAME = "markovdb"

    def __init__(self, filename=None, order=None):
        if not filename: filename = self.DEFAULT_FILENAME

        proxy = ShelveProxy(filename)
        KeyValueModel.__init__(self, proxy=proxy, order=order)
