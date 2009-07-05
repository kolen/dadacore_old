from dadacore.brain import Brain
from dadacore.model import createModel, SequenceTooShortException

def main():
    testm = createModel('berkeley_db')
    br = Brain(testm)
    for line in open('brain.log'):
        try:
            br.learn(line.decode('utf-8'))
        except SequenceTooShortException:
            pass
