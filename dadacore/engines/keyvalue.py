#! /usr/bin/env python

"""
Berkeley db engine -- stores markov model in berkeley db as pickled values
(using standard shelve module).
"""

import random

from dadacore import model

class KeyValueModel(model.AbstractModel):
    """
    Model that stores chain information in berkeley db.
    Uses caching, so call sync() to write dirty cached data from memory to
    database file.
    Non thread-safe, use locking.
    """

    DEFAULT_ORDER = 4

    def __init__(self, proxy, order=None):
        self.db = proxy
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
            raise model.SequenceTooShortException(words)

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
        except model.StartWordException:
            return self._seed_window_dir(start_word, 'b')

    def _seed_window_dir(self, start_word, direction):
        root_key_start = self._root_key(start_word, direction)

        try:
            middle_variants = self.db[root_key_start]
        except KeyError:
            raise model.NoSuchWordException(start_word)

        middle = random.choice(middle_variants.keys())
        assert(isinstance(middle, tuple))

        if start_word is None:
            rightmost = middle_variants[middle]

            assert(isinstance(rightmost, list) or
                   isinstance(rightmost, unicode))
            if isinstance(rightmost, list):
                rightmost = random.choice(rightmost)

            assert(isinstance(rightmost, unicode))
            return middle + (rightmost,)

        if direction == 'f':
            return (start_word,) + middle
        else:
            assert(direction == 'b')
            return middle + (start_word,)

    def sync(self):
        self.db.sync()
