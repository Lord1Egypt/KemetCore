import numpy as np
import struct

def f32(x):
    return np.float32(x)

def bits(x):
    return int(np.float32(x).view(np.uint32))

def frombits(u):
    return np.uint32(u & 0xFFFFFFFF).view(np.float32)

def exp_bits(x):
    # exact float64 math for testing what a simple approximation looks like
    return bits(np.exp(frombits(x)))

if __name__ == "__main__":
    x = f32(-1.0)
    print(np.exp(x))
