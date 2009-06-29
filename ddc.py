#! /usr/bin/env python
import shelve
import re
import sys
import random
from pprint import pprint

class SequenceTooShortException(Exception):
    pass

class MModel:
    DEFAULT_FILENAME = "markovdb"

    def __init__(self, filename=None):
        if not filename: filename = self.DEFAULT_FILENAME
        self.db = shelve.open(filename, writeback=True)

    def _root_key(self, word, direction):
        assert(direction == 'f' or direction == 'b')
        if word is None: word = ''
        return (">%s" if direction == 'f' else "<%s") % word.encode('utf-8')

    def learn(self, words):
        if len(words) < 3:
            raise SequenceTooShortException(words)

        triplet = (None, words[0], words[1])
        for word in words[2:]:
            self._learn_triplet(triplet)
            triplet = (triplet[1], triplet[2], word)
        self._learn_triplet(triplet)
        self._learn_triplet((triplet[1], triplet[2], None))

    def _learn_triplet(self, words):
        for direction in ('f', 'b'):
            self._learn_triplet_dir(words, direction)

    def _learn_triplet_dir(self, words, direction):
        assert(len(words) == 3)

        if direction == 'b':
            words = (words[2], words[1], words[0])

        root_key = self._root_key(words[0], direction)
        if not self.db.has_key(root_key):
            self.db[root_key] = {}
        toplevel = self.db[root_key]

        if not toplevel.has_key(words[1]):
            toplevel[words[1]] = words[2]
        else:
            if isinstance(toplevel[words[1]], unicode):
                if toplevel[words[1]] != words[2]:
                    toplevel[words[1]] = [ toplevel[words[1]], words[2] ]
            elif isinstance(toplevel[words[1]], list):
                if words[2] not in toplevel[words[1]]:
                    toplevel[words[1]].append(words[2])
            else:
                assert(toplevel[words[1]] is None)

                toplevel[words[1]] = words[2]

    def generate_random(self):
        root_key_start = self._root_key(None, 'f')

        first_variants = self.db[root_key_start]
        first = random.choice(first_variants.keys())
        if isinstance(first_variants[first], list):
            second = random.choice(first_variants[first])
        else:
            assert(isinstance(first_variants[first], unicode))
            second = first_variants[first]

        triplet = (None, first, second)
        result = [first, second]

        while 1:
            triplet = (triplet[1], triplet[2])
            first_variants = self.db[self._root_key(triplet[0], 'f')]
            second = first_variants[triplet[1]]

            if isinstance(second, list):
                third = random.choice(second)
            elif isinstance(second, unicode):
                third = second
            else:
                assert(second is None)
                break

            triplet = triplet + (third,)

            result.append(third)

        return result

class Brain:
    def __init__(self, model):
        self.model = model

    def learn(self, string):
        words = self._tokenize(string)
        self.model.learn(words)

    def generate_random(self):
        rwords = self.model.generate_random()
        return self._words_to_string_with_caps(rwords)

    @staticmethod
    def _words_to_string_with_caps(words):
        string = ''
        sentence_start = True
        for word in words:
            if sentence_start:
                string += word[0].upper() + word[1:]
            else:
                string += word
            sentence_start = word[0] in ['.', '?', '!']

        if not sentence_start:
            string += '.'
        return string

    @staticmethod
    def _tokenize(string):
        return [ re.sub("\s+", " ", word).lower() for word in
                 re.findall(r'\w+|\W+', string.strip(), re.UNICODE) ]

testm = MModel()
br = Brain(testm)
for line in open('learn.txt'):
    br.learn(line.decode('utf-8'))

#pprint(testm.db, indent=4)

for i in range(1, 20):
    print br.generate_random()