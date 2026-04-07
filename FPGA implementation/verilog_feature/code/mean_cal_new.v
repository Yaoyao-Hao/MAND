`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/05/19 14:08:31
// Design Name: 
// Module Name: mean_cal_new
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


module mean_cal_new#(
    parameter DATA_W = 32,
    parameter MEAN_NUM = 256,
    parameter WIN    = MEAN_NUM/4,
    parameter MEAN_NUM_W = $clog2(MEAN_NUM),
    parameter WIN_W    = $clog2(WIN)
)
(
    input [0:0] clk_i,
    input [0:0] rst_i,
    input [DATA_W-1:0] DATA_IN,
    input data_in_v,

    output wire data_o_v_o,
    output wire [DATA_W-1:0]data_out_o
    );
reg data_o_v;
reg [DATA_W-1:0]data_out;
 reg [WIN_W:0]cnt_data;
 reg [WIN_W+DATA_W-1:0]add_data;
 reg [WIN_W+DATA_W-1:0]add_data0;
 reg [(WIN_W+DATA_W)*4-1:0]add_save;
 reg add_data_v;
    always@(posedge clk_i or posedge rst_i) begin 
        if(rst_i) begin 
        add_data   <='d0;
        add_data_v <='d0; 
        cnt_data   <='d0;      
        add_data0  <='d0;
        end
            else  begin
                add_data0  <=add_data;
              if(data_in_v) begin
                add_data_v <=(cnt_data>=WIN)?'d1:'d0;  
                add_data <=(cnt_data>=WIN)? DATA_IN:DATA_IN + add_data;
                cnt_data <=(cnt_data>=WIN)? 'd1:cnt_data+ 'd1;
               end
              else begin 
                add_data <= add_data;
                cnt_data <= cnt_data;
                add_data_v <= 'd0;
              end

             end
    end
    reg data_add_start;
always@(posedge clk_i or posedge rst_i) begin
   if(rst_i) begin
    add_save <='d0;
    data_add_start<='d0;
    end
   else      begin
    if(add_data_v) begin 
     add_save <= {add_save[(WIN_W+DATA_W)*3-1:0],add_data0};
     data_add_start<='d1;
    end
    else begin 
        add_save <= add_save;
        data_add_start<='d0;
    end
    end
end
reg [DATA_W +MEAN_NUM_W-1:0 ]add_data_all;
reg  data_add_v;
always@(posedge clk_i or posedge rst_i) begin
   if(rst_i) begin
    add_data_all <='d0;
    data_add_v   <='d0;
    end
   else      begin
    if(data_add_start) begin 
    add_data_all <= add_save[(WIN_W+DATA_W)*1-1:(WIN_W+DATA_W)*0]+add_save[(WIN_W+DATA_W)*2-1:(WIN_W+DATA_W)*1] +
                    add_save[(WIN_W+DATA_W)*3-1:(WIN_W+DATA_W)*2]+add_save[(WIN_W+DATA_W)*4-1:(WIN_W+DATA_W)*3];
    data_add_v   <='d1;    
    end
    else begin
    add_data_all <= add_data_all;
    data_add_v   <='d0;   
    end             
    end
end

always@(posedge clk_i or posedge rst_i) begin
   if(rst_i) begin
    data_o_v <='d0;
    data_out <='d0;
    end
   else      begin
    if(data_add_v) begin 
    data_o_v <='d1;
    data_out <=add_data_all[DATA_W +MEAN_NUM_W-1:MEAN_NUM_W ];  
    end
    else begin
    data_o_v <='d0;
    data_out <=data_out;  
    end             
    end
end
assign  data_o_v_o = data_o_v;
assign  data_out_o = data_out;


endmodule
