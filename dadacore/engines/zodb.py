#! /usr/bin/env python
import re
import sys
import random
from pprint import pprint
from ZODB import FileStorage, DB
from persistent import Persistent
from persistent.mapping import PersistentMapping
from BTrees.OOBTree import OOBTree
import transaction
import dadacore.model

class ZodbModel(dadacore.model.AbstractModel):
    DEFAULT_FILENAME = "markovdb.fs"
    DEFAULT_ORDER = 4

    def __init__(self, filename=None, order=None):
        if not filename: filename = self.DEFAULT_FILENAME
        storage = FileStorage.FileStorage(filename)
        self.db = DB(storage)

        conn = self.db.open()
        root = conn.root()

        if 'config' in root:
            self.order = root['config']['order']
        else:
            if not order: order = self.DEFAULT_ORDER
            self.order = order

            root['config'] = {
                'order': self.order
            }

        if 'f' not in root:
            root['f'] = OOBTree()
        if 'b' not in root:
            root['b'] = OOBTree()

        transaction.commit()

    def learn(self, words):
        """
        Learn sequence of words, by creating transitions in Markov model.
        Words is list of strings.
        """

        conn = self.db.open()
        root = conn.root()

        if __debug__:
            for word in words:
                assert(isinstance(word, unicode))

        ord = self.order
        if len(words) < self.order+1:
            raise dadacore.model.SequenceTooShortException(words)

        window = (None,) + tuple(words[:ord])
        for word in words[ord:]:
            self._learn_window(window, root)
            window = window[1:ord+1] + (word,)
        self._learn_window(window, root)
        self._learn_window(window[1:ord+1] + (None,), root)

        transaction.commit()

    def _learn_window(self, words, root):
        """
        Learn sequence of words. Words must be tuple with count equals to
        model's order + 1.
        """
        for direction in ('f', 'b'):
            self._learn_window_dir(words, direction, root)

    def _learn_window_dir(self, words, direction, root):
        """
        Learn sequence of words in one direction.
        Words must be tuple with count equals to model's order + 1. Direction
        is string and can be 'f' (forward) or 'b' (back).
        """
        ord = self.order
        assert(len(words) == ord+1)

        if direction == 'b':
            words = tuple(reversed(words))

        if words[0] not in root[direction]:
            root[direction][words[0]] = PersistentMapping()
        toplevel = root[direction][words[0]]

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

        toplevel._p_changed = True

    def generate_random(self):
        """
        Generate random sequence of words by traversing from start terminator in
        forward direction.
        Returns list of words, each word is string.
        """

        conn = self.db.open()
        root = conn.root()

        middle_variants = root['f'][None]
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
            middle_variants = root['f'][window[0]]
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
