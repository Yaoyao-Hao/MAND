`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/05/08 09:58:57
// Design Name: 
// Module Name: TB_filter
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


module TB_filter(
    );


    parameter  CLK_PERIOD8 = 8;
    parameter  CLK_PERIOD40 = 100;
    parameter  CLK_PERIOD160 = 25;
    parameter CLK_PERIOD = 10;
    parameter RST_MUL_TIME = 5;

reg sys_clk;
reg sys_clk125;
reg sys_clk160;
reg sys_clk40;
wire clk0;
reg sys_rst;
reg test_st;
reg test_lut;
reg start_a;
reg [3:0]clk_type;

integer j,hand_i,file_handle;
// reg [31:0] mem_signal_in[3000000-1 : 0];

initial begin // initial语句只在程序开始时执行一次
    clk_type = 0;
	sys_clk = 0;
	sys_rst = 1;
	test_st = 0;
    test_lut = 0;
    sys_clk125 = 0;
    sys_clk40  = 0;
    start_a  = 0;
    sys_clk160 = 0;
    // file_handle = $fopen("D:/YCB/YCB/PROJECT/data_Q.txt","r");
    // for (j=0;j<300000;j=j+1)begin
    //     hand_i = $fscanf(file_handle,"%d",mem_signal_in[j]);
    // end
    $fclose(file_handle) ;
	#RST_MUL_TIME sys_rst = 0;
	#10000 test_st = 0;
    #10000 start_a  = 1;
    #10001 start_a  = 0;
    #1000 clk_type = 2;
    //#1000000 begin test_lut =1; test_st = 0;end
     #1000000 begin test_lut =0; test_st = 0; end//1;end
     #100 begin test_lut =0;  end
     #125 begin test_lut =0;  end   
     #1000000 begin test_lut =0; test_st = 1; end//1;end             
     #6000000 begin test_lut =0; test_st = 0;end
     #3000000 begin test_lut =0; test_st = 1;end
end
// 这是一个周期20ns的时钟
always
    #CLK_PERIOD sys_clk = ~sys_clk;
    reg done;
    integer file_id;
    integer i;
    reg [31:0] data_array[300000:0]; // 假设最多读取4个数据
 
    initial begin
        file_id = $fopen("D:/YCB/YCB/PROJECT/EEG_signal_processing/data_MUAQ.txt", "r"); // 打开文件
        if (file_id == 0) begin
            $display("Error: Could not open file");
            done = 0;
        end else begin
            for (i = 0; i < 300000; i = i + 1) begin
                $fscanf(file_id, "%d", data_array[i]); // 读取十进制数
            end
            $fclose(file_id); // 关闭文件
            done = 1; // 完成读取操作
        end
    end





reg [31:0]cnt;
reg [31:0]data_cnt;
wire data_v ;
reg start_a_d;
localparam cnt_Num = 'd1666;//'d100;
always@(posedge sys_clk or posedge sys_rst) begin 
    if(sys_rst) begin cnt<= 'd0;  data_cnt<='d0; start_a_d<= 0;     end
    else      begin cnt<=(cnt<= cnt_Num)? cnt + 'd1:'d0; 
        start_a_d<= #1 start_a;  
        if(data_v) begin
        data_cnt<=data_cnt +'d1; 
        
        end
        else begin
            data_cnt <= data_cnt;
        end
    end
    end

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

wire filter_cal_finish_h;
localparam FILE_NAME   = "D:/YCB/YCB/PROJECT/EEG_signal_processing/fpga_cal_data_mand.txt";
integer    file_handle_wr = 0;
initial begin
    file_handle_wr = $fopen(FILE_NAME,"w");

end
   // assign data_v =(cnt=='d1666)?1:0;//~sys_rst;// (start_a&&~start_a_d)||filter_cal_finish_h;//&cnt;
assign data_v =(cnt==cnt_Num)?1:0;//~sys_rst;// (start_a&&~start_a_d)||filter_cal_finish_h;//&cnt;
    wire [31:0]data_i;
    assign data_i = data_array[data_cnt];

wire data_o_v;
wire signed[31:0]data_o;
//     filter_iir
//     #(
//         .DATA_W (32),
//         .Q      (23),
//         .N       (5)
       
//     )filter_iir_inst(
//         .clk_i   (sys_clk),
//         .rst_i   (sys_rst),
//         .a_i     ({
// a[4],
// a[3],
// a[2],
// a[1],
// a[0]
//         }),
//         .b_i     ({
// b[0],
// b[1],
// b[2],
// b[3],
// b[4]
//         }),
//         .data_i  (data_i),
//         .data_v_i(data_v),
    
//         .data_o  (),
//         .data_v_o()
//         );


//         wire [31:0]a0[1:0];
//         wire [31:0]b0[1:0];
//         assign a0[0] = 'd8388607;
//         assign a0[1] =  -'d7877427;


//         assign b0[0] = 'd8133016;
//         assign b0[1] = - 'd8133017;

        
//         filter_iir
//         #(
//             .DATA_W (32),
//             .Q      (23),
//             .N       (2)
           
//         )filter_iir_inst_2(
//             .clk_i   (sys_clk),
//             .rst_i   (sys_rst),
//             .a_i     ({
//     a0[1],
//     a0[0]
//             }),
//             .b_i     ({
//     b0[0],
//     b0[1]
//             }),
//             .data_i  (data_i),
//             .data_v_i(data_v),
        
//             .data_o  (),
//             .data_v_o()
//             );


 ESA_model
#(
    . DATA_W (32))
    ESA_model_inst
(
.clk_i    (sys_clk),
.rst_i    (sys_rst),
.data_in  (data_i),
.data_in_v(data_v),
.iir_cal_data_v(filter_cal_finish_h),
.data_o_v_o(data_o_v),
.data_out_o(data_o)
    );



//  SBP_model
// #(
//     . DATA_W (32))
//     SBP_model_inst
// (
// .clk_i    (sys_clk),
// .rst_i    (sys_rst),
// .data_in  (data_i),
// .data_in_v(data_v),
// .iir_cal_data_v(filter_cal_finish_h),
// .data_o_v_o(data_o_v),
// .data_out_o(data_o)
//     );

//  MUA_model
// #(
//     . DATA_W (32))
//  MUA_model_inst
// (
// .clk_i    (sys_clk),
// .rst_i    (sys_rst),
// .data_in  (data_i),
// .data_in_v(data_v),
// .iir_cal_data_v(filter_cal_finish_h),
// .data_o_v_o(data_o_v),
// .data_out_o(data_o)
//     );
// MAND#(
//     .DATA_W  (32),
//     .MAND_NUM(15+1))
//     MAND_inst(
//     .clk_i    (sys_clk),
//     .rst_i    (sys_rst),
//     .data_in  (data_i),
//     .data_in_v(data_v),
//     .data_o_v_o (),
//     .data_out_o ()
//     );
    reg [31:0]CNT_file = 'd0;
always@(posedge sys_clk) begin 
 if(data_o_v) begin $fwrite(file_handle_wr, "%d\n", data_o); CNT_file <= CNT_file+ 'd1;
 if (CNT_file == 'd199) begin
     $display("=== 仿真结束：已输出 200 行数据 ===");
     $fclose(file_handle_wr);   // 关闭文件句柄（良好习惯）
     $finish;                   // 结束仿真
 end            
end
end
endmodule
