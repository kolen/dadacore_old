#! /usr/bin/env python
import shelve
import re
import sys
import random
from pprint import pprint
import dadacore.model

class BerkeleyDBModel(dadacore.model.AbstractModel):
    DEFAULT_FILENAME = "markovdb"
    DEFAULT_ORDER = 4

    def __init__(self, filename=None, order=None):
        if not filename: filename = self.DEFAULT_FILENAME
        self.db = shelve.open(filename)
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
            window = window[1:ord+1] + (word,)
        self._learn_window(window)
        self._learn_window(window[1:ord+1] + (None,))

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

        if direction == 'b':
            words = tuple(reversed(words))

        root_key = self._root_key(words[0], direction)
        if not self.db.has_key(root_key):
            self.db[root_key] = {}
        toplevel = self.db[root_key]

        key = words[1:-1]
        rightmost = words[-1]
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
        root_key_start = self._root_key(None, 'f')

        middle_variants = self.db[root_key_start]
        middle = random.choice(middle_variants.keys())
        assert(isinstance(middle, tuple))
        if isinstance(middle_variants[middle], list):
            rightmost = random.choice(middle_variants[middle])
        else:
            assert(isinstance(middle_variants[middle], unicode))
            rightmost = middle_variants[middle]

        window = (None,) + middle + (rightmost,)
        result = list(middle) + [rightmost,]

        assert(len(window) == self.order + 1)

        while 1:
            window = window[1:]
            middle_variants = self.db[self._root_key(window[0], 'f')]
            rightmost_variants = middle_variants[window[1:]]

            if isinstance(rightmost_variants, list):
                rightmost = random.choice(rightmost_variants)
            elif isinstance(rightmost_variants, unicode):
                rightmost = rightmost_variants
            else:
                assert(rightmost_variants is None)
                break

            window = window + (rightmost,)

            result.append(rightmost)

        return result
