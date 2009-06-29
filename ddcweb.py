#! /usr/bin/env python

import web
import ddc

urls = (
  '/', 'index'
)

render = web.template.render('templates/')

mmodel = ddc.MModel()
brain = ddc.Brain(mmodel)

class index:
    def GET(self):
        randomlines = [ brain.generate_random() for i in range(1,10) ]
        return render.index(randomlines)

    def POST(self):
        input = web.input()

        for line in input.learntext.split("\n"):
            try:
                brain.learn(line)
            except ddc.SequenceTooShortException:
                pass

        return render.index([])

app = web.application(urls, globals())

if __name__ == "__main__":
    app.run()