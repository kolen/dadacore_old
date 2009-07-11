import re
from random import randint
from dadacore.model import StartWordException, NoSuchWordException

class BrainIsEmptyException:
    """
    Thrown if brain has not learned anything.
    """

class Brain:
    """
    High-level interface for interaction with Markov model. Can learn lines,
    generate random replies or reply to input line.
    """

    GENERATE_FROM_PHRASE_PICK_COUNT = 5
    GENERATE_FROM_PHRASE_RETRIES_COUNT = 3

    def __init__(self, model):
        self.model = model

    def learn(self, string):
        """
        Learn string. Will throw SequenceTooShortException if string contains
        less number of words that current model order requires.
        """
        assert(isinstance(string, unicode))
        words = self._string_to_words(string)
        self.model.learn(words)

    def generate_random(self):
        """
        Generate random reply as string. Capitalizes first letters when detects
        start of sentence.
        """
        try:
            rwords = self.model.generate_random()
        except NoSuchWordException:
            raise BrainIsEmptyException()
        return self._words_to_string_with_caps(rwords)

    def generate_from_word(self, word):
        """
        Generate reply containing specified word.
        """
        word = word.strip().lower()
        rwords = self.model.generate_from_word(word)
        return self._words_to_string_with_caps(rwords)

    def generate_from_phrase(self, phrase):
        """
        Generate reply to given phrase. Phrase is string with raw line of text.
        """
        words = self._string_to_words(phrase)
        words.sort(key=lambda x: len(x), reverse=True)
        words = words[:self.GENERATE_FROM_PHRASE_PICK_COUNT]

        tries = 0
        while tries < self.GENERATE_FROM_PHRASE_RETRIES_COUNT and words:
            tries += 1
            i = randint(0, len(words)-1)
            selected_word = words[i]
            del words[i]

            try:
                return self.generate_from_word(selected_word)
            except StartWordException:
                continue

        # If all tries generating from word fails, generate random
        return self.generate_random()

    def sync(self):
        """
        Calls sync() on this brain's model
        """
        self.model.sync()

    @staticmethod
    def _words_to_string_with_caps(words):
        """
        Joins list of words to single string, capitalizing first letters of
        words at starts of sentences.
        """
        string = ''
        sentence_start = True
        for word in words:
            if sentence_start:
                string += word[0].upper() + word[1:]
            else:
                string += word
            sentence_start = re.match('[.?!]\s+', word[0])

        if not re.match('[.?!]', word):
            string += '.'
        return string

    @staticmethod
    def _string_to_words(string):
        """
        Splits string into list of words.
        """
        return [ re.sub("\s+", " ", word).lower() for word in
                 re.findall(r'\w+|\W+', string.strip(), re.UNICODE) ]
