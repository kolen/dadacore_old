#! /usr/bin/env python
from __future__ import with_statement
from sys import exc_info
from threading import Lock
import web
from dadacore.model import createModel, SequenceTooShortException, \
    StartWordException
from dadacore.brain import Brain, BrainIsEmptyException

urls = (
  '/', 'index',
  '/reply_to_line', 'reply_to_line',
  '/api/random', 'api_random',
  '/api/reply_to_line', 'api_reply_to_line',
)

render = web.template.render('templates/')

brain_lock = Lock()
with brain_lock:
    mmodel = createModel('berkeley_db')

    brain = Brain(mmodel)

brainlog = open("brain.log", "a")

class index:
    def GET(self):
        try:
            with brain_lock:
                randomlines = [ brain.generate_random() for i in range(1,10) ]
        except BrainIsEmptyException:
            randomlines = [ "Brain is empty" ]
        except StartWordException:
            randomlines = [ "Error: %s %s" % exc_info()[0:1] ]
        return render.index(randomlines)

    def POST(self):
        input = web.input()

        for line in input.learntext.split("\n"):
            brainlog.write("%s\n" % line.strip().encode('utf-8'))
            brainlog.flush()
            try:
                with brain_lock:
                    brain.learn(line)
            except SequenceTooShortException:
                pass

        with brain_lock:
            brain.sync()

        return render.index([])

class reply_to_line:
    def GET(self):
        input = web.input()

        reply = ''
        try:
            with brain_lock:
                reply = brain.generate_from_phrase(input.word)
        except StartWordException:
            reply = "No reply found for this word"

        return render.index([reply])

class api_random:
    def GET(self):
        with brain_lock:
            line = brain.generate_random()
        web.header("Content-type", "text/plain; charset=utf-8")
        return line

class api_reply_to_line:
    def GET(self):
        line = web.input().line
        with brain_lock:
            line = brain.generate_from_phrase(line)
        web.header("Content-type", "text/plain; charset=utf-8")
        return line

app = web.application(urls, globals())

if __name__ == "__main__":
    app.run()