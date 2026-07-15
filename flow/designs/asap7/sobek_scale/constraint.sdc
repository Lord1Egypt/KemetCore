create_clock -name clk -period 9000 [get_ports clk]
set_clock_uncertainty 50 [get_clocks clk]
set_input_delay  [expr 9000*0.1] -clock clk [all_inputs -no_clocks]
set_output_delay [expr 9000*0.1] -clock clk [all_outputs]
