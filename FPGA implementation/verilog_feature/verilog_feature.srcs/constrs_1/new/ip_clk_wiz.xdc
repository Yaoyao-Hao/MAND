#时钟周期约束
create_clock -period 10.000 -name sys_clk_p [get_ports sys_clk_p]
create_clock -period 20.000 -name clk_i [get_ports clk_i]
#时钟复位管脚
set_property -dict {PACKAGE_PIN AE10 IOSTANDARD DIFF_SSTL15} [get_ports sys_clk_p]
set_property IOSTANDARD DIFF_SSTL15 [get_ports sys_clk_n]

set_property  -dict {PACKAGE_PIN AB25 IOSTANDARD LVCMOS33} [get_ports sys_rst_n]

#时钟输出
set_property -dict {PACKAGE_PIN AA20 IOSTANDARD LVCMOS33} [get_ports clk_200m]
set_property -dict {PACKAGE_PIN AB20 IOSTANDARD LVCMOS33} [get_ports clk_200m_180deg]
set_property -dict {PACKAGE_PIN AF22 IOSTANDARD LVCMOS33} [get_ports clk_100m]
set_property -dict {PACKAGE_PIN AG23 IOSTANDARD LVCMOS33} [get_ports clk_25m]
