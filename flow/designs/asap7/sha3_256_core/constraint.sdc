create_clock -name clk -period 2500 [get_ports clk]
set_clock_uncertainty 50 [get_clocks clk]
set_input_delay  [expr 2500*0.1] -clock clk [all_inputs -no_clocks]
set_output_delay [expr 2500*0.1] -clock clk [all_outputs]
# The 1600-bit Keccak state array shares one async reset net across every
# flip-flop — by far the highest-fanout net in any core in this project.
# Without an explicit max_transition target, ORFS's repair_design pass
# doesn't buffer it, leaving 125 slew violations on RESETN pins. 320ps
# matches the ASAP7 library's own reported violation limit.
set_max_transition 300 [current_design]
set_max_fanout 16 [current_design]
