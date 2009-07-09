#! /usr/bin/env python

"""
Berkeley db engine -- stores markov model in berkeley db as pickled values
(using standard shelve module).
"""

import shelve
import random
from time import time
import dadacore.model

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
        self._s = shelve.open(*pargs, **kwargs)
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

class BerkeleyDBModel(dadacore.model.AbstractModel):
    """
    Model that stores chain information in berkeley db.
    Uses caching, so call sync() to write dirty cached data from memory to
    database file.
    Non thread-safe, use locking.
    """

    DEFAULT_FILENAME = "markovdb"
    DEFAULT_ORDER = 4

    def __init__(self, filename=None, order=None):
        if not filename: filename = self.DEFAULT_FILENAME
        self.db = ShelveProxy(filename)
        if self.db.has_key('.config'):
            self.order = self.db['.config']['order']
        else:
            if not order: order = self.DEFAULT_ORDER
            self.order = order
            self._create_config()

    def _create_config(self):
        self.db['.config'] = {
            'order': self.order
        }

    @staticmethod
    def _root_key(word, direction):
        assert(direction == 'f' or direction == 'b')
        if word is None: word = ''
        return (">%s" if direction == 'f' else "<%s") % word.encode('utf-8')

    def learn(self, words):
        """
        Learn sequence of words, by creating transitions in Markov model.
        Words is list of strings.
        """
        ord = self.order
        if len(words) < self.order+1:
            raise dadacore.model.SequenceTooShortException(words)

        window = (None,) + tuple(words[:ord])
        for word in words[ord:]:
            self._learn_window(window)
            window = window[1:] + (word,)
        self._learn_window(window)
        self._learn_window(window[1:] + (None,))

    def _learn_window(self, words):
        """
        Learn sequence of words. Words must be tuple with count equals to
        model's order + 1.
        """
        for direction in ('f', 'b'):
            self._learn_window_dir(words, direction)

    def _learn_window_dir(self, words, direction):
        """
        Learn sequence of words in one direction.
        Words must be tuple with count equals to model's order + 1. Direction
        is string and can be 'f' (forward) or 'b' (back).
        """
        ord = self.order
        assert(len(words) == ord+1)
        assert(not (words[-1] is None and words[-2] is None))

        if direction == 'f':
            root_key = self._root_key(words[0], direction)
        else:
            root_key = self._root_key(words[-1], direction)

        if not self.db.has_key(root_key):
            self.db[root_key] = {}
        toplevel = self.db[root_key]

        key = words[1:-1]
        if direction == 'f':
            rightmost = words[-1]
        else:
            rightmost = words[0]
        if not toplevel.has_key(key):
            toplevel[key] = rightmost
        else:
            if isinstance(toplevel[key], unicode):
                if toplevel[key] != rightmost:
                    toplevel[key] = [ toplevel[key], rightmost ]
            elif isinstance(toplevel[key], list):
                if rightmost not in toplevel[key]:
                    toplevel[key].append(rightmost)
            else:
                assert(toplevel[key] is None)

                toplevel[key] = rightmost

        self.db[root_key] = toplevel

    def generate_random(self):
        """
        Generate random sequence of words by traversing from start terminator in
        forward direction.
        Returns list of words, each word is string.
        """
        window = self._seed_window(None)
        expanded_f = self._expand_window_f(window)
        return list(window) + expanded_f

    def generate_from_word(self, word):
        """
        Generate sequence containing specified word.
        """
        window = self._seed_window(word)

        expanded_f = self._expand_window_f(window)
        expanded_b = self._expand_window_b(window)

        return expanded_b + list(window) + expanded_f

    def _expand_window_f(self, window):
        assert(isinstance(window, tuple))
        assert(len(window) == self.order)

        result = []

        while 1:
            middle_variants = self.db[self._root_key(window[0], 'f')]
            rightmost_variants = middle_variants[window[1:]]

            if isinstance(rightmost_variants, list):
                rightmost = random.choice(rightmost_variants)
                if rightmost is None:
                    break
            elif isinstance(rightmost_variants, unicode):
                rightmost = rightmost_variants
            else:
                assert(rightmost_variants is None)
                break

            window = window + (rightmost,)

            result.append(rightmost)
            window = window[1:]

        return result

    def _expand_window_b(self, window):
        assert(isinstance(window, tuple))
        assert(len(window) == self.order)

        result = []

        while 1:
            middle_variants = self.db[self._root_key(window[-1], 'b')]
            rightmost_variants = middle_variants[window[:-1]]

            if isinstance(rightmost_variants, list):
                rightmost = random.choice(rightmost_variants)
                if rightmost is None:
                    break
            elif isinstance(rightmost_variants, unicode):
                rightmost = rightmost_variants
            else:
                assert(rightmost_variants is None)
                break

            window = (rightmost,) + window

            result.insert(0, rightmost)
            window = window[:-1]

        return result

    def _seed_window(self, start_word):
        try:
            return self._seed_window_dir(start_word, 'f')
        except dadacore.model.StartWordException:
            return self._seed_window_dir(start_word, 'b')

    def _seed_window_dir(self, start_word, direction):
        root_key_start = self._root_key(start_word, direction)

        try:
            middle_variants = self.db[root_key_start]
        except KeyError:
            raise dadacore.model.NoSuchWordException(start_word)

        middle = random.choice(middle_variants.keys())
        assert(isinstance(middle, tuple))
        if isinstance(middle_variants[middle], list):
            rightmost = random.choice(middle_variants[middle])
            if rightmost is None:
                raise dadacore.model.StartWordSequenceTooShortException(start_word)
        else:
            assert(isinstance(middle_variants[middle], unicode))
            rightmost = middle_variants[middle]

        return middle + (rightmost,)

    def sync(self):
        self.db.sync()
