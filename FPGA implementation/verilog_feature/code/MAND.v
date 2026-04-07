`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/05/15 14:51:14
// Design Name: 
// Module Name: MAND
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


module MAND#(
    parameter DATA_W = 32,
    parameter MAND_NUM = 15
    )(
    input [0:0] clk_i,
    input [0:0] rst_i,
    input [DATA_W-1:0]data_in,
    input data_in_v,
    output             data_o_v_o,
    output [DATA_W-1:0]data_out_o

    );
             wire   data_o_v;
wire[DATA_W-1:0]data_out;

 reg [DATA_W*MAND_NUM-1:0]data_lut;
 reg [DATA_W*MAND_NUM-1:0]data_lut_b;
reg data_in_v_cal;
wire [DATA_W-1:0]MAND_delta;

 always@(posedge clk_i or posedge rst_i) begin 
 if(rst_i) begin
    data_lut <='d0;
  end
 else      begin
   if(data_in_v) begin
    data_lut <= {data_lut[DATA_W*(MAND_NUM-1)-1:0],data_in};
    end
   else begin
    data_lut <= data_lut;
    end
  end 
end


//  always@(posedge clk_i or posedge rst_i) begin 
//  if(rst_i) begin
//     data_lut_b <='d0;
//   end
//  else      begin
//    if(data_in_v) begin
//     data_lut_b <= {data_lut_b[DATA_W*(MAND_NUM-1)-1:0],MAND_delta};
//     end
//    else begin
//     data_lut_b <= data_lut_b;
//     end
//   end 
// end


 always@(posedge clk_i or posedge rst_i) begin 
 if(rst_i) begin
    data_in_v_cal <='d0;
  end
 else      begin
    data_in_v_cal <=#1 data_in_v;
  end 
end

wire [DATA_W-1:0]MAND_B,MAND_A;
assign MAND_B = data_lut[DATA_W*(MAND_NUM)-1:DATA_W*(MAND_NUM-1)];
assign MAND_A = data_lut[DATA_W-1:0];



assign MAND_delta = MAND_A - MAND_B;
wire [DATA_W-1:0]MAND_delta_abs;
assign MAND_delta_abs = MAND_delta[DATA_W-1]?~MAND_delta:MAND_delta;

               //     mean_cal#(
               //      .DATA_W   (DATA_W),
               //      .MEAN_NUM (4096)
               //     )mean_cal_inst
               //  (
               //      .clk_i    (clk_i),
               //      .rst_i    (rst_i),
               //      .DATA_IN  (MAND_delta_abs),
               //      .data_in_v(data_in_v_cal),
               //      .data_o_v(data_o_v),
               //      .data_out(data_out)
               //      );

mean_cal_new#(
                    .DATA_W   (DATA_W),
                    .MEAN_NUM (4096)
                   )mean_cal_inst
(
    .clk_i    (clk_i),
    .rst_i    (rst_i),
    .DATA_IN  (MAND_delta_abs),
    .data_in_v(data_in_v_cal),
    .data_o_v_o (data_o_v),
    .data_out_o (data_out)
    );

// wire downsamp_data_v0;
// reg [DATA_W-1:0]downsamp_data0;
//             down_samp
//             #(
//                .down_num('d1500)
//             )down_samp_inst_50
//             (
//             .clk_i   (clk_i),
//             .rst_i   (rst_i),
//             .data_v  (data_o_v),
//             .data_v_o(downsamp_data_v0)
//                 );
//                 always@(posedge clk_i or posedge rst_i) begin 
//                     if(rst_i) begin
//                         downsamp_data0 <='d0;
//                      end
//                     else      begin
//                        if(downsamp_data_v0) begin
//                         downsamp_data0 <= data_out;
//                         end
//                        else begin
//                         downsamp_data0 <= downsamp_data0 ;
//                         end
//                      end 
//                    end
assign data_o_v_o = data_o_v;
assign data_out_o = data_out;



endmodule
