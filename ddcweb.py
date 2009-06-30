#! /usr/bin/env python
from __future__ import with_statement
import web
import ddc
from threading import Lock

urls = (
  '/', 'index'
)

render = web.template.render('templates/')

brain_lock = Lock()
with brain_lock:
    mmodel = ddc.MModel()
    brain = ddc.Brain(mmodel)
    brain.learn(u"Test test test.")

brainlog = open("brain.log", "w")

class index:
    def GET(self):
        with brain_lock:
            randomlines = [ brain.generate_random() for i in range(1,10) ]
        return render.index(randomlines)

    def POST(self):
        input = web.input()

        for line in input.learntext.split("\n"):
            brainlog.write("%s\n" % line.strip().encode('utf-8'))
            try:
                with brain_lock:
                    brain.learn(line)
            except ddc.SequenceTooShortException:
                pass

        return render.index([])

app = web.application(urls, globals())

if __name__ == "__main__":
    app.run()