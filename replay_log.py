#!/usr/bin/python

from dadacore.brain import Brain
from dadacore.model import createModel, SequenceTooShortException
from sys import stderr

def main():
    testm = createModel('berkeley_db')
    br = Brain(testm)
    for line in open('brain.log'):
        stderr.write(".")
        try:
            br.learn(line.decode('utf-8'))
        except SequenceTooShortException:
            pass
    stderr.write("\n")
    br.sync()

if __name__ == "__main__":
    main()