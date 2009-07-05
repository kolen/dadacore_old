#! /usr/bin/env python

import re
from dadacore.brain import Brain
from dadacore.model import createModel, SequenceTooShortException

def main():
    testm = createModel('berkeley_db')
    br = Brain(testm)
    for line in open('learn.txt'):
        try:
            br.learn(line.decode('utf-8'))
        except SequenceTooShortException:
            pass

    #pprint(testm.db, indent=4)

    for i in range(1, 20):
        print br.generate_random()
        print

if __name__ == "__main__":
    main()
