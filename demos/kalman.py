from functools import partial
from random import random
from threading import Thread
import time
import math
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Slider
from bokeh.plotting import curdoc, figure, output_file, show
from bokeh.layouts import row, widgetbox

import numpy as np
import numpy.matlib as mat
import numpy.random as rnd

from tornado import gen

INTERACTIVE=True

COUNT = 300
t = 0

# The actual state of our system (constant value)
realx = [-0.37727] * COUNT
#realx = [math.sin(x/12.0) for x in range(0,COUNT-1)]

# Our simulated measurements: realx + a normal (Gaussian) noise
def generate_noisy_data(data):
    return [[x + rnd.normal(0, 0.1)] for x in data]

z = generate_noisy_data(realx)

# Our initial estimate of the system's state
x = [mat.matrix([0])]

# Initialise our matrices
P = [mat.zeros((1,1))]
H = mat.identity(1)
Q = mat.matrix([0.0001])
K = [mat.zeros((1,1))]
R = mat.matrix([0.01])

def kalman(t):
    # Prediction phase

    # x[t|t-1] = x[t-1|t-1]
    x_prior = x[t-1]
    # P[t|t-1] = P[t-1|t-1] + Q
    P_prior = P[t-1] + Q

    # Measurement update (correction) phase
    K.append(P_prior * H.T / ( H * P_prior * H.T + R ))
    x.append(x_prior + K[t] * (z[t] - H * x_prior))
    P.append((mat.identity(1) - K[t] * H) * P_prior)


#######################################################

if not INTERACTIVE:

    for i in range(0, COUNT-1):
        kalman(t)
        t += 1

    # output to static HTML file
    output_file("lines.html")

    # create a new plot with a title and axis labels
    p = figure(title="Kalman filter", x_axis_label='steps', y_axis_label='variable')

    # add a line renderer with legend and line thickness
    p.circle(range(0, COUNT), z, legend="Measurements")
    p.line(range(0, COUNT), realx, legend="Real value", line_width=2, line_color="orange", line_dash="4 4")
    p.line(range(0, COUNT), x, legend="Kalman output", line_width=2, line_color="green")

    # show the results
    show(p)

else:

    def update_data(attrname, old, new):
        measures = [target.value] * (COUNT-t)
        noisy_measures = generate_noisy_data(measures)

        realx[t:] = measures
        z[t:] = noisy_measures

    target = Slider(title="Actual value", value=realx[0], start=-5.0, end=5.0, step=0.1)
    target.on_change('value', update_data)


    # this must only be modified from a Bokeh session allback
    source = ColumnDataSource(data=dict(idx=[0], est=[x[0][0,0]],measure=z[0],real=[realx[0]]))

    # This is important! Save curdoc() to make sure all threads
    # see then same document.
    doc = curdoc()

    @gen.coroutine
    def update(t, est, measure, real):
        source.stream(dict(idx=[t], est=[est], measure=[measure], real=[real]))

    def blocking_task():
        global t,COUNT

        while t < COUNT:
            # do some blocking computation
            time.sleep(0.2)
            kalman(t)

            estimate = x[-1][0,0]

            # but update the document from callback
            doc.add_next_tick_callback(partial(update,
                                                t=t,
                                                est=estimate,
                                                measure=z[t][0],
                                                real=realx[t]))

            t += 1

    p = figure(x_range=[0, COUNT])
    l = p.circle(x='idx', y='measure', source=source, legend="Measurements")
    p.line(x='idx', y='real', source=source, legend="Real value", line_width=2, line_color="orange", line_dash="4 4")
    p.line(x='idx', y='est', source=source, legend="Kalman output", line_width=2, line_color="green")

    doc.add_root(row(widgetbox(target),p,width=800))

    thread = Thread(target=blocking_task)
    thread.start()
