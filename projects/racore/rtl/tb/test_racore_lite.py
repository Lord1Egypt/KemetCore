"""cocotb testbench for RaCore-Lite."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

@cocotb.test()
async def test_racore_lite_boot(dut):
    """Test that RaCore-Lite compiles and resets without crashing."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst.value = 1
    dut.load_en.value = 0
    dut.load_addr.value = 0
    dut.load_data.value = 0
    
    for _ in range(5):
        await RisingEdge(dut.clk)
        
    dut.rst.value = 0
    
    for _ in range(10):
        await RisingEdge(dut.clk)
        
    # Just verify it doesn't x-propagate everywhere immediately
    assert dut.dbg_pc.value.is_resolvable, "PC is unresolved X/Z"
    
