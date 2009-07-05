
class SequenceTooShortException(Exception):
    pass

class AbstractModel:
    def learn(self, words):
        """
        Learn sequence of words, by creating transitions in Markov model.
        Words is list of strings.
        """

    def generate_random(self):
        """
        Generate random sequence of words by traversing from start terminator in
        forward direction.
        Returns list of words, each word is string.
        """
