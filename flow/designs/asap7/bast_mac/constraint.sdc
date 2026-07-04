# bast_mac: single clock, relaxed 4 ns period (250 MHz) for a clean first close.
create_clock -name clk -period 4000 [get_ports clk]
set_clock_uncertainty 50 [get_clocks clk]
set_input_delay  200 -clock clk [all_inputs -no_clocks]
set_output_delay 200 -clock clk [all_outputs]
