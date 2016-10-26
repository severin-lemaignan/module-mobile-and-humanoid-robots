from numpy.matlib import matrix
import numpy.random as rnd

COUNT=150

NOISE_VARIANCE=0.06

NOISE_VARIANCE=0.04

SCALE = 0.00001

g = 9.8 * SCALE

realx = [matrix([[1.],[0.]])]
for i in range(COUNT-1):
    xprev, vprev = realx[i]
    realx.append([xprev + vprev - g/2, vprev -g])


# Our simulated measurements: realx + a normal (Gaussian) noise
def generate_noisy_data(data):
    return [x[0] + rnd.normal(0, NOISE_VARIANCE) for x in data]

z = generate_noisy_data(realx)


def reset_state():
    global k, x, P

    # Our initial estimate of the system's state
    x = [matrix([[0.5],[0.]])] # [x, v]
    P = [matrix([[0.001, 0.],[0., 0.001]])]

    k = 1

# Initialise our state
k = 0
x = []
P = []
reset_state()

# Initialise our matrices
F = matrix([[1.,1.],[0.,1.]]) # based on the free fall equations
B = matrix([[0.5],[1.]]) # the contribution of the gravity g (based on the free fall equations)
H = matrix([1.,0.]) # we only measure the height, not the velocity

Q = matrix([[0.],[0.]]) # no process noise
R = matrix([0.001]) # initial estimate of our position measurement noise

u = matrix([-g]) # control input: gravity

def kalman(k):
    # Prediction phase
    x_prior = F * x[k-1] + B * u
    P_prior = F * P[k-1] * F.T + Q

    # Measurement update (correction) phase
    K = P_prior * H.T * ( H * P_prior * H.T + R ).I
    x.append(x_prior + K * (z[k] - H * x_prior))
    P.append((matrix([[1,0],[0,1]]) - K * H) * P_prior)


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
                        real=[realx[0]])
    pause = False

def togglepause():
    global pause
    pause = not pause

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


noisevariance = Slider(title="Noise variance", value=NOISE_VARIANCE, start=0.001, end=0.2, step=0.001)
noisevariance.on_change('value', set_noise_variance)

measurementnoise = Slider(title="Measurement noise R", value=R[0,0], start=0.0001, end=0.01, step=0.0001)
measurementnoise.on_change('value', set_measurement_noise)



# this must only be modified from a Bokeh session callback
source = ColumnDataSource(data=dict(idx=[0],
                                    est=[x[0][0,0]],
                                    measure=[z[0][0,0]],
                                    real=[realx[0]]
                                    ))

# This is important! Save curdoc() to make sure all threads
# see then same document.
doc = curdoc()

@gen.coroutine
def update(step, est, measure, real):
    source.stream(dict(idx=[step], est=[est], measure=[measure], real=[real]))

def blocking_task():
    global k,COUNT

    while True: # run forever -> this allow to restart the plot even after we've reached COUNT
        
        while k < COUNT:

            if pause:
                time.sleep(0.2)
                continue

            # do some blocking computation
            kalman(k)

            estimate = x[-1][0][0,0]

            # but update the document from callback
            doc.add_next_tick_callback(partial(update,
                                                step=k,
                                                est=estimate,
                                                measure=z[k][0,0],
                                                real=realx[k][0]))

            k += 1

            time.sleep(0.2)

        time.sleep(0.2)

p = figure(plot_height=400, plot_width=400,
           x_range=[0, COUNT], y_range=[0,1.2])

l = p.circle(x='idx', y='measure', source=source, legend="Measurements")
p.line(x='idx', y='real', source=source, legend="Real value", line_width=2, line_color="orange", line_dash="4 4")
p.line(x='idx', y='est', source=source, legend="Kalman output", line_width=2, line_color="green")

doc.add_root(row(widgetbox(startbutton, pausebutton, noisevariance, measurementnoise),p,width=800))

thread = Thread(target=blocking_task)
thread.start()
