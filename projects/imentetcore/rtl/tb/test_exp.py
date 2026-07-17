import os
import cocotb
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue
import struct
import numpy as np
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../../../..'))
from projects.imentetcore.golden.imentet_fp32 import exp_bits, bits, frombits

@cocotb.test()
async def test_imentet_exp(dut):
    """Test the fp32 exp unit against the bit-exact python golden model."""
    
    test_cases = [
        0.0,
        -1.0,
        -0.5,
        -0.1,
        -10.0,
        -5.5,
        -80.0,
        -87.0,
        -88.0,
        -100.0
    ]
    
    # Add random test cases
    np.random.seed(42)
    for _ in range(100):
        test_cases.append(float(np.random.uniform(-87.0, 0.0)))

    for x in test_cases:
        x_bits = bits(x)
        expected_y_bits = exp_bits(x_bits)
        
        dut.x.value = x_bits
        await Timer(1, units="ns")
        
        actual_y_bits = int(dut.y.value)
        
        if actual_y_bits != expected_y_bits:
            a_val = frombits(actual_y_bits)
            e_val = frombits(expected_y_bits)
            assert False, f"Mismatch at x={x} (0x{x_bits:08X}): Expected 0x{expected_y_bits:08X} ({e_val}), got 0x{actual_y_bits:08X} ({a_val})"

    print(f"Verified {len(test_cases)} cases successfully.")
