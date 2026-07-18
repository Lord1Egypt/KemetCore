import numpy as np
import sys
import os

# Add KemetCore to path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../..'))
from projects.imentetcore.golden.imentet_fp32 import *

errs = []
for x in np.linspace(-10, 0, 100):
    a = frombits(exp_bits(bits(x)))
    e = np.exp(x)
    err = abs(a-e)/e
    if err > 1e-4:
        print(f"x={x} a={a} e={e} err={err}")
