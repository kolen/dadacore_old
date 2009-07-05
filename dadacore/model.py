
class SequenceTooShortException(Exception):
    pass

class ModelCreationException(Exception):
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

def createModel(type, *pargs, **kwargs):
    if type not in models:
        raise ModelCreationException("No such model type: %s" % type)
    else:
        return models[type](*pargs, **kwargs)

def _createBerkeleyDbModel(*pargs, **kwargs):
    from dadacore.engines.berkeley_db import BerkeleyDBModel
    return BerkeleyDBModel(*pargs, **kwargs)

def _createZodbModel(*pargs, **kwargs):
    from dadacore.engines.zodb import ZodbModel
    return ZodbModel(*pargs, **kwargs)

models = {
    'berkeley_db': _createBerkeleyDbModel,
    'zodb': _createZodbModel,
}