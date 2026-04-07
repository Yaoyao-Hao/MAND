`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/05/08 09:05:32
// Design Name: 
// Module Name: filter_iir
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


module filter_iir
#(
    parameter DATA_W = 32,
    parameter Q      = 24,
    parameter N      =  2
)(
    input clk_i,
    input rst_i,
    //input [3:0] N,

    input [N*DATA_W-1:0]a_i,
    input [N*DATA_W-1:0]b_i,
    input [DATA_W-1:0] data_i,
    input              data_v_i,

    output [DATA_W-1:0] data_o,
    output              data_v_o
    );

    reg [2:0]STATE;
    localparam INIT   =   0,
               CAL_A    = 1,
               WAIT_CLA = 2,
               CAL_B    = 3,
               WAIT_CLB = 4,
               ADD      = 5,
               FINISH   = 6;
    reg [3:0]cal_cnt;
    reg mult_cal_v;
    reg [15:0]mult_cal_v_d;
    wire mult_cal_finish;
    assign mult_cal_finish = mult_cal_v_d[7];
    reg [DATA_W-1:0]w_a,w_b;
    reg [DATA_W-1:0]w ;
    reg w_v;
    always@(posedge clk_i or posedge rst_i) begin 
        if(rst_i) begin 
            mult_cal_v_d<= 'd0;   
             end
        else      begin 
            mult_cal_v_d<= {mult_cal_v_d[6:0],mult_cal_v};
         end
        end
    

    reg [DATA_W*N-1:0]x_shift;

    reg [DATA_W*N-1:0]y_shift;

    always@(posedge clk_i or posedge rst_i) begin 
        if(rst_i) begin 
            x_shift<= 'd0;   
             end
        else      begin 
            if(data_v_i) begin
            x_shift<= {x_shift[DATA_W*(N-1)-1:0],data_i};
            end
            else begin 
                x_shift<= x_shift;  
            end
         end
        end
    always@(posedge clk_i or posedge rst_i) begin 
        if(rst_i) begin 
            y_shift<= 'd0;
             end
        else      begin 
            if(data_v_o) begin
                y_shift<= {y_shift[DATA_W*(N-1)-1:0],data_o};
            end
            else begin 
                y_shift<= y_shift;  
            end
         end
        end
    wire [DATA_W+Q-1:Q]p_OUT;
    reg cal_A_B;
    always@(posedge clk_i or posedge rst_i) begin 
        if(rst_i) begin
            STATE <= INIT;
            cal_cnt <='d0;
            mult_cal_v <= 'd0;
            cal_A_B<='d0;
            w_a <='d0;
            w_b <='d0;
            w   <='d0;
            w_v <='d0;
        end 
        else begin 
            case(STATE)
            INIT  :begin  
                w_a <='d0;
                w_b <='d0;
                w   <=w;
                w_v <='d0;
                cal_cnt <='d0;
                cal_A_B<='d0;
                if(data_v_i) begin 
                    STATE <= CAL_A;
                    mult_cal_v <= 'd1;
                 end
                else         begin 
                    STATE <= INIT ;
                    mult_cal_v <= 'd0;
                 end
            end
            CAL_A :begin  
                cal_A_B<='d0;
                if(mult_cal_finish) begin 
                    STATE <= WAIT_CLA;
                    mult_cal_v <= 'd0;
                    cal_cnt <=cal_cnt + 'd1;
                    w_a <=w_a + p_OUT;
                    w_b <='d0;
                 end
                else         begin 
                    STATE <= CAL_A ;
                    mult_cal_v <= 'd0;
                    cal_cnt <=cal_cnt;
                    w_a <=w_a;
                    w_b <='d0;
                 end           
            end
            WAIT_CLA:begin 
                if(cal_cnt < N ) begin 
                    STATE <= CAL_A;
                    mult_cal_v <= 'd1;
                    cal_cnt <=cal_cnt;
                    cal_A_B<='d0;
                    w_a <=w_a;
                    w_b <='d0;
                 end
                else         begin 
                    STATE <= CAL_B ;
                    mult_cal_v <= 'd1;
                    cal_cnt <= 1;
                    cal_A_B<='d1;
                    w_a <=w_a;
                    w_b <='d0;
                 end 
            end
            CAL_B :begin  
                cal_A_B<='d1;
                if(mult_cal_finish) begin 
                    STATE <= WAIT_CLB;
                    mult_cal_v <= 'd0;
                    cal_cnt <=cal_cnt + 'd1;
                    w_a <=w_a;
                    w_b <=w_b + p_OUT;
                 end
                else         begin 
                    STATE <= CAL_B ;
                    mult_cal_v <= 'd0;
                    cal_cnt <=cal_cnt;
                    w_a <=w_a;
                    w_b <=w_b;
                 end 
            end
            WAIT_CLB:begin 
                cal_A_B<='d1;
                if(cal_cnt < N ) begin 
                    STATE <= CAL_B;
                    mult_cal_v <= 'd1;
                    cal_cnt <=cal_cnt;
                    w_a <=w_a;
                    w_b <=w_b;
                 end
                else         begin 
                    STATE <= ADD ;
                    mult_cal_v <= 'd0;
                    cal_cnt <= 0;
                    w_a <=w_a;
                    w_b <=w_b;
                 end 
            end
            ADD   :begin  
                cal_A_B<='d1;
                STATE <= FINISH ;
                w_a <=w_a;
                w_b <=w_b;
                w   <=w_a - w_b;
                w_v <='d0;
            end
            FINISH:begin  
                cal_A_B<='d0;
                STATE <= INIT ;
                w_a <=0;
                w_b <=0;
                w   <= w;
                w_v <='d1;
            end
            endcase
        end
    end

    assign data_o = w;
    assign data_v_o = w_v;
    reg [DATA_W-1:0]A,B;
    wire [DATA_W*2-1:0]P;
  

generate 
	case(N)
		'd2:begin
        always@(*) begin 
         case(cal_cnt) 
           'd0:begin      A =cal_A_B? y_shift[DATA_W*(1)-1:DATA_W*(0)]:x_shift[DATA_W*(1)-1:DATA_W*(0)]     ; B = cal_A_B? a_i[DATA_W*(1)-1:DATA_W*(0)]:b_i[DATA_W*(1)-1:DATA_W*(0)]; end
           'd1:begin      A =cal_A_B? y_shift[DATA_W*(2-1)-1:DATA_W*(1-1)]:x_shift[DATA_W*(2)-1:DATA_W*(1)] ; B = cal_A_B? a_i[DATA_W*(2)-1:DATA_W*(1)]:b_i[DATA_W*(2)-1:DATA_W*(1)]; end
            default:begin A =cal_A_B? y_shift[DATA_W*(1)-1:DATA_W*(0)]:x_shift[DATA_W*(1)-1:DATA_W*(0)]     ; B = cal_A_B? a_i[DATA_W*(1)-1:DATA_W*(0)]:b_i[DATA_W*(1)-1:DATA_W*(0)]; end
      
         endcase
        end
		end     
       	'd3:begin
        always@(*) begin 
         case(cal_cnt) 
           'd0:begin      A =cal_A_B? y_shift[DATA_W*(1)-1:DATA_W*(0)]:x_shift[DATA_W*(1)-1:DATA_W*(0)]     ; B = cal_A_B? a_i[DATA_W*(1)-1:DATA_W*(0)]:b_i[DATA_W*(1)-1:DATA_W*(0)]; end
           'd1:begin      A =cal_A_B? y_shift[DATA_W*(2-1)-1:DATA_W*(1-1)]:x_shift[DATA_W*(2)-1:DATA_W*(1)] ; B = cal_A_B? a_i[DATA_W*(2)-1:DATA_W*(1)]:b_i[DATA_W*(2)-1:DATA_W*(1)]; end
           'd2:begin      A =cal_A_B? y_shift[DATA_W*(3-1)-1:DATA_W*(2-1)]:x_shift[DATA_W*(3)-1:DATA_W*(2)] ; B = cal_A_B? a_i[DATA_W*(3)-1:DATA_W*(2)]:b_i[DATA_W*(3)-1:DATA_W*(2)]; end
            default:begin A =cal_A_B? y_shift[DATA_W*(1)-1:DATA_W*(0)]:x_shift[DATA_W*(1)-1:DATA_W*(0)]     ; B = cal_A_B? a_i[DATA_W*(1)-1:DATA_W*(0)]:b_i[DATA_W*(1)-1:DATA_W*(0)]; end
      
         endcase
        end
		end     
		'd5:begin 
        always@(*) begin 
         case(cal_cnt) 
           'd0:begin      A =cal_A_B? y_shift[DATA_W*(1)-1:DATA_W*(0)]:x_shift[DATA_W*(1)-1:DATA_W*(0)]     ; B = cal_A_B? a_i[DATA_W*(1)-1:DATA_W*(0)]:b_i[DATA_W*(1)-1:DATA_W*(0)]; end
           'd1:begin      A =cal_A_B? y_shift[DATA_W*(2-1)-1:DATA_W*(1-1)]:x_shift[DATA_W*(2)-1:DATA_W*(1)] ; B = cal_A_B? a_i[DATA_W*(2)-1:DATA_W*(1)]:b_i[DATA_W*(2)-1:DATA_W*(1)]; end
           'd2:begin      A =cal_A_B? y_shift[DATA_W*(3-1)-1:DATA_W*(2-1)]:x_shift[DATA_W*(3)-1:DATA_W*(2)] ; B = cal_A_B? a_i[DATA_W*(3)-1:DATA_W*(2)]:b_i[DATA_W*(3)-1:DATA_W*(2)]; end
           'd3:begin      A =cal_A_B? y_shift[DATA_W*(4-1)-1:DATA_W*(3-1)]:x_shift[DATA_W*(4)-1:DATA_W*(3)] ; B = cal_A_B? a_i[DATA_W*(4)-1:DATA_W*(3)]:b_i[DATA_W*(4)-1:DATA_W*(3)]; end
           'd4:begin      A =cal_A_B? y_shift[DATA_W*(5-1)-1:DATA_W*(4-1)]:x_shift[DATA_W*(5)-1:DATA_W*(4)] ; B = cal_A_B? a_i[DATA_W*(5)-1:DATA_W*(4)]:b_i[DATA_W*(5)-1:DATA_W*(4)]; end
            default:begin A =cal_A_B? y_shift[DATA_W*(1)-1:DATA_W*(0)]:x_shift[DATA_W*(1)-1:DATA_W*(0)]     ; B = cal_A_B? a_i[DATA_W*(1)-1:DATA_W*(0)]:b_i[DATA_W*(1)-1:DATA_W*(0)]; end
      
         endcase
        end
		end     

     endcase
endgenerate







    

    mult_gen_0 mult_gen_inst (
        .CLK(clk_i),  // input wire CLK
        .A(A),      // input wire [31 : 0] A
        .B(B),      // input wire [31 : 0] B
        .P(P)      // output wire [63 : 0] P
      );
assign p_OUT = P[DATA_W*2-1:Q];





//       wire [DATA_W*N-1:0]x_shift_a[N-1:0];

//       wire [DATA_W*N-1:0]y_shift_a[N-1:0];
// genvar i;
//       generate 
//         for(i=0;i<=N;i=i+1) begin:test_tb
//           assign   x_shift_a[i] = x_shift[(i+1)*DATA_W-1:i*DATA_W];
//           assign   y_shift_a[i] = y_shift[(i+1)*DATA_W-1:i*DATA_W];
//       end
//       endgenerate

endmodule
