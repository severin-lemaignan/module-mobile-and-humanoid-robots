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
### PLOTTING
#######################################################
#######################################################

from bokeh.plotting import figure, output_file, show



for i in range(0, COUNT-1):
    kalman(k)
    k += 1

# output to static HTML file
output_file("lines.html")

# create a new plot with a title and axis labels
p = figure(x_axis_label='steps', y_axis_label='variable',y_range=[-1,1],x_range=[0,COUNT])

# add a line renderer with legend and line thickness
p.circle(range(0, COUNT), z, legend="Measurements")
p.line(range(0, COUNT), realx, legend="Real value", line_width=2, line_color="orange", line_dash="4 4")
p.line(range(0, COUNT), x, legend="Kalman output", line_width=2, line_color="green")
p.line(range(0, COUNT), Ks, legend="Kalman gain", line_width=1, line_color="blue")

# show the results
show(p)

