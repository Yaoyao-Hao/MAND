`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/11/11 16:13:52
// Design Name: 
// Module Name: MUA_model
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


module MUA_model#(
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

localparam N =3;
localparam INIT     = 0,
           FILTER_B = 1,
           FINISH   = 2;

           wire [31:0]a[4:0];
           wire [31:0]b[4:0];
           
           assign a[0] = 'd8388607;
           assign a[1] = -'d16156323;
           assign a[2] = 'd7789887;
           
           assign b[0] = 'd8083704;
           assign b[1] = - 'd16167409;
           assign b[2] = 'd8083704;

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
    a_iir        <= {a[2],a[1],a[0]}; 
    b_iir        <= {b[0],b[1],b[2]};
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
    a_iir        <= {a[2],a[1],a[0]}; 
    b_iir        <= {b[0],b[1],b[2]};
         end
        else begin
            STATE <= INIT;
            data_in_cal  <= data_in_cal;
            filter_h_cal <= 'd0;
            filter_l_cal <= 'd0;
    a_iir        <= {a[2],a[1],a[0]}; 
    b_iir        <= {b[0],b[1],b[2]};
         end
    end
    FILTER_B: begin 
        if(filter_cal_finish_h) begin
            STATE <= FINISH;
            data_in_cal  <= data_out_iir_h[DATA_W-1]?~data_out_iir_h:data_out_iir_h;
            filter_h_cal <= 'd0;
            filter_l_cal <= 'd1;
    a_iir        <= {a[2],a[1],a[0]}; 
    b_iir        <= {b[0],b[1],b[2]};
         
        end
        else begin
            STATE <= FILTER_B;
            data_in_cal  <= data_in_cal;
            filter_h_cal <= 'd0;
            filter_l_cal <= 'd0;
    a_iir        <= {a[2],a[1],a[0]}; 
    b_iir        <= {b[0],b[1],b[2]};
         end
    end
    FINISH  : begin 
        STATE <= INIT;
        data_in_cal  <= data_in_cal;
        iir_cal_data_v<='d1;
    a_iir        <= {a[2],a[1],a[0]}; 
    b_iir        <= {b[0],b[1],b[2]};
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
reg [5:0]data_spike_cal;
wire signed[DATA_W-1:0]thr_data;
assign thr_data = -'d802426326;
wire signed[DATA_W-1:0]data_cal;
assign data_cal = data_out_iir_h;
wire spike_data;
assign spike_data = (data_cal > thr_data);
reg iir_cal_data_v_d;
always@(posedge clk_i or posedge rst_i) begin 
 if(rst_i) begin data_spike_cal <='d0;
iir_cal_data_v_d<=#1 'd0;
end
 else      begin
    iir_cal_data_v_d<=#1 iir_cal_data_v;
    if(iir_cal_data_v) begin data_spike_cal<= {data_spike_cal[4:0],spike_data}; end
    else               begin data_spike_cal<= data_spike_cal ;                           end    
  end
 end
wire spike_edge;
assign spike_edge = ~data_spike_cal[1]&&data_spike_cal[0];
reg [10:0]cnt;
reg [10:0]bined_spike;
reg bined_spike_v;
reg [1:0]STATE_CAL_BIN;
always@(posedge clk_i or posedge rst_i) begin 
 if(rst_i) begin 
   cnt<='d0;
   STATE_CAL_BIN <='d0;
   bined_spike <='d0;
   bined_spike_v<='d0;
  end
 else      begin
    case(STATE_CAL_BIN)
     'd0:begin
      
           if(iir_cal_data_v_d) begin cnt<=(cnt<'d1499)? cnt + 'd1:'d0;
                                    STATE_CAL_BIN <=(cnt<'d1499)?'d0:'d1;   
                                    bined_spike <= bined_spike + spike_edge;       
                                    bined_spike_v<=(cnt>='d1499);        
        end
         else               begin cnt<= cnt; 
                                  STATE_CAL_BIN <=STATE_CAL_BIN;
                                  bined_spike <= bined_spike;
                                  bined_spike_v<='d0;
        end
      end
     'd1:begin
        STATE_CAL_BIN <='d0;
        cnt<= cnt;
        bined_spike <= 'd0;
        bined_spike_v<='d0;
      end 
    endcase
  end
 end
reg [10:0]lut0,lut1,lut2,lut3;
reg bined_spike_v_d;
always@(posedge clk_i or posedge rst_i) begin 
 if(rst_i)
 begin
lut0<= 'd0;
lut1<= 'd0;
lut2<= 'd0;
lut3<= 'd0;
bined_spike_v_d<='d0;
  end
 else 
 begin
  if(bined_spike_v) begin
bined_spike_v_d<=#1 bined_spike_v;
lut0<= bined_spike;
lut1<= lut0;
lut2<= lut1;
lut3<= lut2;
  end
else begin 
bined_spike_v_d<='d0;
lut0<= lut0;
lut1<= lut1;
lut2<= lut2;
lut3<= lut3;
end
  end
end
wire [12:0]data_o;
assign data_o = lut0 +lut1 +lut2 +lut3;
assign data_o_v_o = bined_spike_v_d;
assign data_out_o = {19'd0,data_o};
// reg [31:0]test_cnt;
// always@(posedge clk_i or posedge rst_i) begin 
//  if(rst_i) begin test_cnt <='d0;
// end
//  else      begin
//     if(iir_cal_data_v) begin test_cnt<= test_cnt+'d1; end
//     else               begin test_cnt<= test_cnt ;                           end    
//   end
//  end

endmodule
