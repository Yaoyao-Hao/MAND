`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/05/09 13:38:53
// Design Name: 
// Module Name: mean_cal
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


module mean_cal#(
    parameter DATA_W = 32,
    parameter MEAN_NUM = 256,
    parameter MEAN_NUM_W = $clog2(MEAN_NUM)
)
(
    input [0:0] clk_i,
    input [0:0] rst_i,
    input [DATA_W-1:0] DATA_IN,
    input data_in_v,

    output reg data_o_v,
    output reg [DATA_W-1:0]data_out
    );

wire [13:0]data_count;
wire rd_en;
wire [DATA_W-1:0]dout;
wire [DATA_W-1:0]dout_cal;
assign rd_en = (data_count<= MEAN_NUM)? 0:data_in_v;
assign dout_cal  = (data_count<= MEAN_NUM)? 0:dout;
    fifo_mean fifo_mean_inst (
  .clk(clk_i),                // input wire clk
  .srst(rst_i),              // input wire srst
  .din(DATA_IN),                // input wire [31 : 0] din
  .wr_en(data_in_v),            // input wire wr_en
  .rd_en(rd_en),            // input wire rd_en
  .dout(dout),              // output wire [31 : 0] dout
  .full(full),              // output wire full
  .empty(empty),            // output wire empty
  .data_count(data_count)  // output wire [13 : 0] data_count
);

localparam INIT   = 0,
           ADD    = 1,
           CAL    = 2,
           FINISH = 3; 

reg [2:0]STATE;
reg [DATA_W+MEAN_NUM_W-1:0]ADD_DATA;
always@(posedge clk_i or posedge rst_i) begin 
 if(rst_i) begin 
    STATE <= INIT;
    ADD_DATA <= 'd0;
    data_out <='d0;
    data_o_v <='d0;
 end
 else      begin 
case(STATE)
INIT   :begin 
        data_out <=data_out;
    data_o_v <='d0;
    if(data_in_v) begin
        STATE <= ADD;
        ADD_DATA <= ADD_DATA + {{MEAN_NUM_W{DATA_IN[DATA_W-1]}},DATA_IN};
    end
    else          begin
        STATE <= INIT;
        ADD_DATA <= ADD_DATA ;
    end
end
ADD    :begin 
            data_out <=data_out;
    data_o_v <='d0;
    ADD_DATA <= ADD_DATA - {{MEAN_NUM_W{DATA_IN[DATA_W-1]}},dout_cal} ; 
    STATE <= CAL;
end
CAL    :begin 
    data_out <=ADD_DATA[DATA_W+MEAN_NUM_W-1:MEAN_NUM_W];
    data_o_v <='d1;
    STATE <= FINISH;
    ADD_DATA <= ADD_DATA;
end
FINISH :begin 
    data_out <=data_out;
    data_o_v <='d0;
    STATE <= INIT;
    ADD_DATA <= ADD_DATA;
end
endcase
 end
end



endmodule
