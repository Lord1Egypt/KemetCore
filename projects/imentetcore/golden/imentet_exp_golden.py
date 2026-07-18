import numpy as np
import struct

def frombits(u):
    return np.uint32(u & 0xFFFFFFFF).view(np.float32)

def bits(x):
    return int(np.float32(x).view(np.uint32))

# LUT for 2^(i/16) for i in 0..15 in fp32
LUT_2_POW = [
    bits(2**(i/16.0)) for i in range(16)
]

def exp_approx_bits(xb):
    """
    Fixed-order fp32 datapath simulation for imentet_exp.
    xb is 32-bit pattern of fp32 x.
    1. Check bounds
    2. Multiply x by log2(e) (fp32)
    3. Extract I_shift and F_val
    4. Compute LUT + Taylor
    5. Adjust exponent
    """
    x = frombits(xb)
    if x > 0:
        return bits(1.0)
    if x < -87.33654: # -126 * ln(2)
        return bits(0.0)
        
    # Constant c = log2(e) in fp32
    c = np.float32(1.44269504)
    y = np.float32(np.float32(x) * c)
    
    # y is negative. Let y_pos = -y
    y_pos = np.float32(-y)
    
    # In hardware, extract integer via fp32-to-int truncate
    I_pos = int(y_pos)
    # Re-convert to fp32 to find F_pos
    F_pos = np.float32(np.float32(y_pos) - np.float32(I_pos))
    
    if F_pos == 0.0:
        I_shift = I_pos
        F_val = np.float32(0.0)
    else:
        I_shift = I_pos + 1
        F_val = np.float32(np.float32(1.0) - F_pos)
        
    # Multiply F_val by 16 to get LUT index
    # We can do this in hardware by adding 4 to exponent
    f_16 = np.float32(F_val * 16.0)
    idx = int(f_16)
    rem = np.float32(np.float32(F_val) - np.float32(idx / 16.0))
    
    # Read LUT
    lut_val = frombits(LUT_2_POW[idx])
    
    # Compute poly: 1 + rem * ln2 + 0.5 * (rem * ln2)^2
    # In hardware: 
    ln2 = np.float32(0.69314718)
    r_ln2 = np.float32(rem * ln2)
    term2 = np.float32(np.float32(np.float32(0.5) * r_ln2) * r_ln2)
    poly = np.float32(np.float32(1.0) + np.float32(r_ln2 + term2))
    
    res = np.float32(lut_val * poly)
    
    # Exponent adjustment
    res_b = bits(res)
    exp_field = (res_b >> 23) & 0xFF
    if exp_field >= I_shift:
        res_b = (res_b & 0x807FFFFF) | ((exp_field - I_shift) << 23)
        return res_b
    else:
        return bits(0.0)

def exp_approx(x):
    return frombits(exp_approx_bits(bits(x)))

if __name__ == "__main__":
    errs = []
    for x in np.linspace(-10, 0, 1000):
        a = exp_approx(x)
        e = np.exp(x)
        errs.append(abs(a-e)/e)
    print(f"Max rel err: {max(errs):.2e}")
