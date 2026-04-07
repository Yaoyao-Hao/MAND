`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/05/13 09:52:08
// Design Name: 
// Module Name: SBP_model
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


module SBP_model#(
    parameter DATA_W = 32)(
    input [0:0] clk_i,
    input [0:0] rst_i,
    input [DATA_W-1:0]data_in,
    input data_in_v,
    output             data_o_v_o,
    output [DATA_W-1:0]data_out_o,
    output reg iir_cal_data_v

    );
             wire   data_o_v;
wire[DATA_W-1:0]data_out;

localparam N =5;
localparam INIT     = 0,
           FILTER_B = 1,
           FINISH   = 2;

           wire [31:0]a[4:0];
           wire [31:0]b[4:0];
           
           assign a[0] = 'd8388607;
           assign a[1] = - 'd31611013;
           assign a[2] = 'd44896037;
           assign a[3] = -'d28490159;
           assign a[4] = 'd6817837;
           
           assign b[0] = 'd40782;
           assign b[1] =  'd0;
           assign b[2] = -'d81565;
           assign b[3] = 0;
           assign b[4] = 'd40782;

reg [3:0]STATE;
wire filter_cal_finish_l;
wire filter_cal_finish_h;
reg filter_h_cal,filter_l_cal;
reg [DATA_W-1:0]data_in_cal;
wire[DATA_W-1:0]data_out_iir_h;
wire[DATA_W-1:0]data_out_iir_l;
wire [DATA_W-1:0]iir_cal_data;
//reg iir_cal_data_v;
reg [DATA_W*N-1:0]a_iir;
reg [DATA_W*N-1:0]b_iir;
always@(posedge clk_i or posedge rst_i) begin 
 if(rst_i) begin
    STATE <= INIT;
    filter_h_cal <= 'd0;
    filter_l_cal <= 'd0;
    data_in_cal  <= 'd0;
    iir_cal_data_v<='d0;
    a_iir        <= {a[4],a[3],a[2],a[1],a[0]}; 
    b_iir        <= {b[0],b[1],b[2],b[3],b[4]};
  end
 else      begin
    case(STATE)
    INIT    : begin 
        iir_cal_data_v<='d0;
        if(data_in_v) begin
            STATE <= FILTER_B;
            data_in_cal  <= data_in;
            filter_h_cal <= 'd1;
            filter_l_cal <= 'd0;
    a_iir        <= {a[4],a[3],a[2],a[1],a[0]}; 
    b_iir        <= {b[0],b[1],b[2],b[3],b[4]};
         end
        else begin
            STATE <= INIT;
            data_in_cal  <= data_in_cal;
            filter_h_cal <= 'd0;
            filter_l_cal <= 'd0;
    a_iir        <= {a[4],a[3],a[2],a[1],a[0]}; 
    b_iir        <= {b[0],b[1],b[2],b[3],b[4]};
         end
    end
    FILTER_B: begin 
        if(filter_cal_finish_h) begin
            STATE <= FINISH;
            data_in_cal  <= data_out_iir_h[DATA_W-1]?~data_out_iir_h:data_out_iir_h;
            filter_h_cal <= 'd0;
            filter_l_cal <= 'd1;
    a_iir        <= {a[4],a[3],a[2],a[1],a[0]}; 
    b_iir        <= {b[0],b[1],b[2],b[3],b[4]};
         
        end
        else begin
            STATE <= FILTER_B;
            data_in_cal  <= data_in_cal;
            filter_h_cal <= 'd0;
            filter_l_cal <= 'd0;
    a_iir        <= {a[4],a[3],a[2],a[1],a[0]}; 
    b_iir        <= {b[0],b[1],b[2],b[3],b[4]};
         end
    end
    FINISH  : begin 
        STATE <= INIT;
        data_in_cal  <= data_in_cal;
        iir_cal_data_v<='d1;
    a_iir        <= {a[4],a[3],a[2],a[1],a[0]}; 
    b_iir        <= {b[0],b[1],b[2],b[3],b[4]};
    end
    endcase
  end
end

    filter_iir
    #(
        .DATA_W (32),
        .Q      (23),
        .N       (N)
       
    )filter_iir_inst_h(
        .clk_i   (clk_i),
        .rst_i   (rst_i),
        .a_i     (a_iir),
        .b_i     (b_iir),
        .data_i  (data_in_cal),
        .data_v_i(filter_h_cal),
    
        .data_o  (data_out_iir_h),
        .data_v_o(filter_cal_finish_h)
        );
wire downsamp_data_v;
reg [DATA_W-1:0]downsamp_data;
            down_samp
            #(
               .down_num('d15)
            )down_samp_inst
            (
            .clk_i   (clk_i),
            .rst_i   (rst_i),
            .data_v  (iir_cal_data_v),
            .data_v_o(downsamp_data_v)
                );
                always@(posedge clk_i or posedge rst_i) begin 
                    if(rst_i) begin
                        downsamp_data <='d0;
                     end
                    else      begin
                       if(downsamp_data_v) begin
                        downsamp_data <= data_in_cal;
                        end
                       else begin
                        downsamp_data <= downsamp_data ;
                        end
                     end 
                   end
                   mean_cal_new#(
                    .DATA_W   (DATA_W),
                    .MEAN_NUM (512)
                   )mean_cal_inst
                (
                    .clk_i    (clk_i),
                    .rst_i    (rst_i),
                    .DATA_IN  (downsamp_data),
                    .data_in_v(downsamp_data_v),
                    .data_o_v_o(data_o_v),
                    .data_out_o(data_out)
                    );
            wire downsamp_data_v0;
            reg [DATA_W-1:0]downsamp_data0;
            down_samp
            #(
               .down_num('d100)
            )down_samp_inst_50
            (
            .clk_i   (clk_i),
            .rst_i   (rst_i),
            .data_v  (data_o_v),
            .data_v_o(downsamp_data_v0)
                );
                always@(posedge clk_i or posedge rst_i) begin 
                    if(rst_i) begin
                        downsamp_data0 <='d0;
                     end
                    else      begin
                       if(downsamp_data_v0) begin
                        downsamp_data0 <= data_out;
                        end
                       else begin
                        downsamp_data0 <= downsamp_data0 ;
                        end
                     end 
                   end
assign data_o_v_o = downsamp_data_v0;
assign data_out_o = downsamp_data0;
endmodule
