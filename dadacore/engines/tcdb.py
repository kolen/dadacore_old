"""
Tokyo Cabinet storage engine, based on generic key-value store.
'tc' module is required to use this:
  http://github.com/rsms/tc
"""

try:
    from cPickle import loads, dumps
except ImportError:
    from pickle import loads, dumps
import tc
from keyvalue import KeyValueModel

class TcProxy():
    def __init__(self, filename):
        self.hdb = tc.HDB()
        self.hdb.open(filename, tc.HDBOWRITER | tc.HDBOCREAT)

    def __getitem__(self, key):
        return loads(self.hdb[key])

    def __setitem__(self, key, value):
        self.hdb[key] = dumps(value)

    def has_key(self, key):
        return self.hdb.has_key(key)

class TcdbModel(KeyValueModel):

    DEFAULT_FILENAME = "markovdb.tch"

    def __init__(self, filename=None, order=None):
        if not filename: filename = self.DEFAULT_FILENAME

        proxy = TcProxy(filename)
        KeyValueModel.__init__(self, proxy=proxy, order=order)
