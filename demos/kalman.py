from functools import partial
from random import random
from threading import Thread
import time
import math
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Slider, Button
from bokeh.plotting import curdoc, figure, output_file, show
from bokeh.layouts import row, widgetbox

import numpy as np
import numpy.matlib as mat
import numpy.random as rnd

from tornado import gen

INTERACTIVE=True

COUNT = 150
t = 0

# The actual state of our system (constant value)
realx = [-0.37727] * COUNT
#realx = [math.sin(x/12.0) for x in range(0,COUNT-1)]

# Our simulated measurements: realx + a normal (Gaussian) noise
def generate_noisy_data(data):
    return [[x + rnd.normal(0, 0.1)] for x in data]

z = generate_noisy_data(realx)

# Our initial estimate of the system's state
x = None
P = None

def reset_state():
    global t, x, P

    t = 0

    # Our initial estimate of the system's state
    x = [mat.zeros(1)]
    P = [mat.zeros((1,1))]

reset_state()

# Initialise our matrices
H = mat.identity(1)
Q = mat.matrix([0.0001])
R = mat.matrix([0.01])


def kalman(t):
    # Prediction phase

    # x[t|t-1] = x[t-1|t-1]
    x_prior = x[t-1]
    # P[t|t-1] = P[t-1|t-1] + Q
    P_prior = P[t-1] + Q

    # Measurement update (correction) phase
    K = P_prior * H.T / ( H * P_prior * H.T + R )
    x.append(x_prior + K * (z[t] - H * x_prior))
    P.append((mat.identity(1) - K * H) * P_prior)


#######################################################

if not INTERACTIVE:

    for i in range(0, COUNT-1):
        kalman(t)
        t += 1

    # output to static HTML file
    output_file("lines.html")

    # create a new plot with a title and axis labels
    p = figure(x_axis_label='steps', y_axis_label='variable',y_range=[-1,1])

    # add a line renderer with legend and line thickness
    p.circle(range(0, COUNT), z, legend="Measurements")
    p.line(range(0, COUNT), realx, legend="Real value", line_width=2, line_color="orange", line_dash="4 4")
    #p.line(range(0, COUNT), x, legend="Kalman output", line_width=2, line_color="green")

    # show the results
    show(p)

else:

    pause = False

    def restart():
        print("Restarting the plot")

        reset_state()

        source.data=dict(idx=[0], est=[x[0][0,0]],measure=z[0],real=[realx[0]])

    def togglepause():
        global pause
        pause = not pause

    def update_data(attrname, old, new):
        global realx,z
        print("Updating target value to %s" % target.value)
        realx = [target.value] * COUNT
        z = generate_noisy_data(realx)

    def set_measurement_noise(attrname, old, new):
        global R
        print("Updating measurement noise to %s" % measurementnoise.value)
        R = mat.matrix([measurementnoise.value])

    startbutton = Button(label="Restart", button_type="success")
    startbutton.on_click(restart)

    pausebutton = Button(label="Pause", button_type="warning")
    pausebutton.on_click(togglepause)


    target = Slider(title="Actual value", value=realx[0], start=-5.0, end=5.0, step=0.1)
    target.on_change('value', update_data)

    measurementnoise = Slider(title="Measurement noise", value=R[0,0], start=0, end=0.1, step=0.001)
    measurementnoise.on_change('value', set_measurement_noise)



    # this must only be modified from a Bokeh session callback
    source = ColumnDataSource(data=dict(idx=[0], est=[x[0][0,0]],measure=z[0],real=[realx[0]]))

    # This is important! Save curdoc() to make sure all threads
    # see then same document.
    doc = curdoc()

    @gen.coroutine
    def update(t, est, measure, real):
        source.stream(dict(idx=[t], est=[est], measure=[measure], real=[real]))

    def blocking_task():
        global t,COUNT

        while True: # run forever -> this allow to restart the plot even after we've reached COUNT
            
            while t < COUNT:

                if pause:
                    time.sleep(0.2)
                    continue

                # do some blocking computation
                kalman(t)

                estimate = x[-1][0,0]

                # but update the document from callback
                doc.add_next_tick_callback(partial(update,
                                                    t=t,
                                                    est=estimate,
                                                    measure=z[t][0],
                                                    real=realx[t]))

                t += 1

                time.sleep(0.1)

            time.sleep(0.2)

    p = figure(x_range=[0, COUNT])
    l = p.circle(x='idx', y='measure', source=source, legend="Measurements")
    p.line(x='idx', y='real', source=source, legend="Real value", line_width=2, line_color="orange", line_dash="4 4")
    p.line(x='idx', y='est', source=source, legend="Kalman output", line_width=2, line_color="green")

    doc.add_root(row(widgetbox(startbutton, pausebutton, target, measurementnoise),p,width=800))

    thread = Thread(target=blocking_task)
    thread.start()
