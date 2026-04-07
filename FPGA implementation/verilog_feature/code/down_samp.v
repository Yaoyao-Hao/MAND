`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/05/09 11:18:25
// Design Name: 
// Module Name: down_samp
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module down_samp
#(
   parameter  down_num = 'd100 
)
(
input clk_i,
input rst_i,
input data_v,
output reg data_v_o
    );

reg [31:0]cnt_data;
always@(posedge clk_i or posedge rst_i) begin 
 if(rst_i) begin
    cnt_data <='d0;
    data_v_o <='d0;
  end
 else      begin
    if(data_v) begin
        cnt_data <= (cnt_data< down_num-'d1)? cnt_data+ 'd1:'d0;
        data_v_o <= (|cnt_data)?  0           :data_v;
     end
    else begin
        cnt_data <= cnt_data ;
        data_v_o <='d0;
     end
  end 
end



endmodule
