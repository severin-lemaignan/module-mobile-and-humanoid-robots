from numpy.matlib import matrix
import numpy.random as rnd

COUNT=150

NOISE_VARIANCE=0.06

# The actual state of our system (constant value)
realx = [-0.37727] * COUNT

# Our simulated measurements: realx + a normal (Gaussian) noise
def generate_noisy_data(data):
    return [matrix([x + rnd.normal(0, NOISE_VARIANCE)]) for x in data]

z = generate_noisy_data(realx)


def reset_state():
    global k, x, P, Ks

    # Our initial estimate of the system's state at step k=0
    x = [matrix([0.])]
    P = [matrix([0.001])]

    Ks = []
    k = 1

# Initialise our state
k = 0
x = []
P = []
Ks = [] # store the Kalman gains (for plotting purpose only)
reset_state()

# Initialise our matrices
F = matrix([1.]) # we assume our state to be constant
B = matrix([0.]) # no control input
H = matrix([1.]) # direct measure of the value

Q = matrix([0.]) # no process noise
R = matrix([0.001]) # estimate of our measurement noise

u = matrix([0.]) # no control input

def kalman(k):
    # Prediction phase
    x_prior = F * x[k-1] + B * u
    P_prior = F * P[k-1] * F.T + Q

    # Measurement update (correction) phase
    K = P_prior * H.T * ( H * P_prior * H.T + R ).I
    Ks.append(K[0,0])
    x.append(x_prior + K * (z[k] - H * x_prior))
    P.append((matrix([1]) - K * H) * P_prior)


#######################################################
#######################################################
### INTERACTIVE PLOTTING
#######################################################
#######################################################

from functools import partial
from threading import Thread
import time
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Slider, Button
from bokeh.plotting import curdoc, figure
from bokeh.layouts import row, widgetbox
from tornado import gen

pause = False

def restart():
    global pause
    print("Restarting the plot")

    reset_state()

    source.data=dict(idx=[0],
                        est=[x[0][0,0]],
                        measure=[z[0][0,0]],
                        real=[realx[0]],
                        gain=[0])
    pause = False

def togglepause():
    global pause
    pause = not pause

def update_data(attrname, old, new):
    global realx,z
    print("Updating target value to %s" % target.value)
    realx = [target.value] * COUNT
    z = generate_noisy_data(realx)

def set_noise_variance(attrname, old, new):
    global NOISE_VARIANCE,z
    print("Updating noise variance to %s" % noisevariance.value)
    NOISE_VARIANCE = noisevariance.value
    z = generate_noisy_data(realx)


def set_measurement_noise(attrname, old, new):
    global R
    print("Updating measurement noise to %s" % measurementnoise.value)
    R = matrix([measurementnoise.value])

startbutton = Button(label="Restart", button_type="success")
startbutton.on_click(restart)

pausebutton = Button(label="Pause", button_type="warning")
pausebutton.on_click(togglepause)


target = Slider(title="Actual value", value=realx[0], start=-1.0, end=0.0, step=0.1)
target.on_change('value', update_data)

noisevariance = Slider(title="Noise variance", value=NOISE_VARIANCE, start=0.001, end=0.2, step=0.001)
noisevariance.on_change('value', set_noise_variance)

measurementnoise = Slider(title="Measurement noise R", value=R[0,0], start=0.0001, end=0.01, step=0.0001)
measurementnoise.on_change('value', set_measurement_noise)



# this must only be modified from a Bokeh session callback
source = ColumnDataSource(data=dict(idx=[0],
                                    est=[x[0][0,0]],
                                    measure=[z[0][0,0]],
                                    real=[realx[0]],
                                    gain=[0]
                                    ))

# This is important! Save curdoc() to make sure all threads
# see then same document.
doc = curdoc()

@gen.coroutine
def update(step, est, measure, real, gain):
    source.stream(dict(idx=[step], est=[est], measure=[measure], real=[real], gain=[gain]))

def blocking_task():
    global k,COUNT

    while True: # run forever -> this allow to restart the plot even after we've reached COUNT
        
        while k < COUNT:

            if pause:
                time.sleep(0.2)
                continue

            # do some blocking computation
            kalman(k)

            estimate = x[-1][0,0]

            # but update the document from callback
            doc.add_next_tick_callback(partial(update,
                                                step=k,
                                                est=estimate,
                                                measure=z[k][0,0],
                                                real=realx[k],
                                                gain=Ks[k-1]))

            k += 1

            time.sleep(0.2)

        time.sleep(0.2)

p = figure(plot_height=400, plot_width=400,
           x_range=[0, COUNT], y_range=[-1,0])

l = p.circle(x='idx', y='measure', source=source, legend="Measurements")
p.line(x='idx', y='real', source=source, legend="Real value", line_width=2, line_color="orange", line_dash="4 4")
p.line(x='idx', y='est', source=source, legend="Kalman output", line_width=2, line_color="green")
p.line(x='idx', y='gain', source=source, legend="Kalman gain", line_width=1, line_color="blue")

doc.add_root(row(widgetbox(startbutton, pausebutton, target, noisevariance, measurementnoise),p,width=800))

thread = Thread(target=blocking_task)
thread.start()
