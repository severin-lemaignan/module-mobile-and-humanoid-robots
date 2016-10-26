Kalman demos
============

<img alt="Example of a Kalman filter output when measuring a free-falling object with noise" src="https://raw.githubusercontent.com/severin-lemaignan/module-mobile-and-humanoid-robots/master/figs/kalman-ex2-final.png" width="400">

The scripts in this directory show how a simple Kalman filter can be implemented
in Python.

These scripts require the [Bokeh](http://bokeh.pydata.org) plotting library.
Install it with `pip install bokeh`.

Run the static examples with:

```
$ python kalman-constant.py
$ python kalman-freefall.py
```

Run the interactive examples with:

```
$ bokeh serve --show kalman-constant-interactive.py
$ bokeh serve --show kalman-freefall-interactive.py
```
