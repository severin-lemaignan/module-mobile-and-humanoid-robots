from numpy.matlib import matrix
import numpy.random as rnd

COUNT=150

NOISE_VARIANCE=0.04

# "scale" the gravity to have a nicer plot
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
### PLOTTING
#######################################################
#######################################################

from bokeh.plotting import figure, output_file, show

for i in range(0, COUNT-1):
    kalman(k)
    k += 1

# output to static HTML file
output_file("output.html")

# create a new plot with a title and axis labels
p = figure(x_axis_label='steps', y_axis_label='variable',y_range=[0,1.2],x_range=[0,COUNT])

# add a line renderer with legend and line thickness
p.circle(range(0, COUNT), [zt[0,0] for zt in z], legend="Measurements")
p.line(range(0, COUNT), [h for h,v in realx], legend="Real value", line_width=2, line_color="orange", line_dash="4 4")
p.line(range(0, COUNT), [xt[0,0] for xt in x], legend="Kalman output", line_width=2, line_color="green")

# show the results
show(p)


