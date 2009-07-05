#! /usr/bin/env python

import re
from dadacore.brain import Brain
from dadacore.model import createModel, SequenceTooShortException

def main():
    testm = createModel('berkeley_db')
    br = Brain(testm)

    for i in range(1, 20):
        print br.generate_random()
        print

if __name__ == "__main__":
    main()
