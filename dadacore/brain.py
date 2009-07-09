import re

class Brain:
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
        rwords = self.model.generate_random()
        return self._words_to_string_with_caps(rwords)

    def generate_from_word(self, word):
        word = word.strip().lower()
        rwords = self.model.generate_from_word(word)
        return self._words_to_string_with_caps(rwords)

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
            sentence_start = re.match('[.?!]', word[0])

        if not sentence_start:
            string += '.'
        return string

    @staticmethod
    def _string_to_words(string):
        """
        Splits string into list of words.
        """
        return [ re.sub("\s+", " ", word).lower() for word in
                 re.findall(r'\w+|\W+', string.strip(), re.UNICODE) ]
