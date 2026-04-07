#include <zephyr/kernel.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/logging/log.h>
#include <assert.h>
#include <zephyr/kernel.h>

#include <zephyr/sys/ring_buffer.h>
#include <zephyr/types.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <errno.h>
#include <soc.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/sys_clock.h>

LOG_MODULE_REGISTER(main, LOG_LEVEL_DBG);

#define UART_DEVICE_NODE DT_NODELABEL(uart0)
#define RAW_DATA_SIZE 30
#define WINDOW_SIZE 200
#define FRAME_TOTAL_LEN (2 + 30 * 4 + 1) 
#define STEP_SIZE 50
#define BLOCK_SIZE 50     
#define BLOCK_SUMS_SIZE 4 

static float current_block_sum = 0.0f; 
static int current_block_count = 0;    

static float block_sums[BLOCK_SUMS_SIZE] = {0};
static int block_sum_idx = 0;
static float window_sum = 0.0f;
static int valid_blocks = 0;


struct uart_rx_context
{
    uint8_t packet[FRAME_TOTAL_LEN]; 
    size_t recv_cnt;                 
    int64_t last_recv_ts;            
    bool frame_valid;                
};

static uint8_t rx_bufs[2][FRAME_TOTAL_LEN];
static bool current_buf = 0;
static uint8_t tx_buf[FRAME_TOTAL_LEN];

static struct uart_rx_context rx_ctx;
struct uart_config config;


#define MAX_PENDING_PACKETS 10
K_MSGQ_DEFINE(uart_msgq, FRAME_TOTAL_LEN, MAX_PENDING_PACKETS, 4);

#define PROCESSING_STACK_SIZE 4096
K_THREAD_STACK_DEFINE(processing_stack, PROCESSING_STACK_SIZE); 

static struct k_thread processing_thread; 
void processing_thread_func(void);


typedef struct
{

    float hp_x_prev;
    float hp_y_prev;


    float lp_x_prev;
    float lp_y_prev;
} filter_state_t;


static filter_state_t filter_state = {0};


static const float hp_coeff[] = {0.96953125f, -0.96953125f, -0.93906251f}; // b0, b1, a1
static const float lp_coeff[] = {0.00125506f, 0.00125506f, -0.99748988f};  // b0, b1, a1


const struct device *uart_dev = DEVICE_DT_GET(UART_DEVICE_NODE);


static inline float high_pass_filter(float input, filter_state_t *state)
{
    float output = hp_coeff[0] * input +
                   hp_coeff[1] * state->hp_x_prev -
                   hp_coeff[2] * state->hp_y_prev;
    state->hp_x_prev = input;
    state->hp_y_prev = output;
    return output;
}

static inline float low_pass_filter(float input, filter_state_t *state)
{
    float output = lp_coeff[0] * input +
                   lp_coeff[1] * state->lp_x_prev -
                   lp_coeff[2] * state->lp_y_prev;
    state->lp_x_prev = input;
    state->lp_y_prev = output;
    return output;
}


static void uart_cb(const struct device *dev, struct uart_event *evt, void *user_data)
{
    static enum { WAIT_HEADER,
                  COLLECT_DATA } state = WAIT_HEADER;
    static uint8_t packet[FRAME_TOTAL_LEN];
    static uint16_t index = 0;

    // LOG_INF("enter callback");
    switch (evt->type)
    {
    case UART_RX_RDY:
        uint8_t *data = evt->data.rx.buf + evt->data.rx.offset;
        int64_t now = k_uptime_get() * NSEC_PER_MSEC;

        uart_rx_buf_rsp(dev, evt->data.rx.buf, FRAME_TOTAL_LEN);

        
        if ((now - rx_ctx.last_recv_ts) > 50 * NSEC_PER_MSEC && rx_ctx.recv_cnt > 0)
        {
            LOG_WRN("Frame timeout, reset buffer");
            rx_ctx.recv_cnt = 0;
        }

        for (int i = 0; i < evt->data.rx.len; i++)
        {
            switch (state)
            {
            case WAIT_HEADER:
                if (index == 0 && data[i] == 0xAA)
                {
                    packet[index++] = data[i];
                }
                else if (index == 1 && data[i] == 0x55)
                {
                    packet[index++] = data[i];
                    state = COLLECT_DATA;
                }
                else
                {
                    index = 0;
                }
                break;

            case COLLECT_DATA:
                packet[index++] = data[i];
                if (index >= FRAME_TOTAL_LEN)
                {
                    
                    uint8_t checksum = 0;
                    for (int j = 0; j < FRAME_TOTAL_LEN - 1; j++)
                    {
                        checksum += packet[j];
                    }

                    if ((checksum & 0xFF) == packet[FRAME_TOTAL_LEN - 1])
                    {
                        k_msgq_put(&uart_msgq, packet, K_NO_WAIT);
                    }

                    state = WAIT_HEADER;
                    index = 0;
                }
                break;
            }
        }

        break;

    case UART_RX_BUF_REQUEST:
        
        uart_rx_buf_rsp(dev, rx_bufs[current_buf], FRAME_TOTAL_LEN);
        current_buf = !current_buf;

        break;
    }

    if (evt->type == UART_RX_RDY)
    {
    }
}


static void uart_rx_init(void)
{

    uart_config_get(uart_dev, &config);
    
    config.baudrate = 115200;
    config.parity = UART_CFG_PARITY_NONE;
    config.stop_bits = UART_CFG_STOP_BITS_1;
    config.data_bits = UART_CFG_DATA_BITS_8;
    config.flow_ctrl = UART_CFG_FLOW_CTRL_NONE; 
    uart_configure(uart_dev, &config);

    uart_rx_enable(uart_dev, rx_bufs[0], FRAME_TOTAL_LEN, 0);
    uart_rx_buf_rsp(uart_dev, rx_bufs[1], FRAME_TOTAL_LEN);
}


void processing_thread_func(void)
{
    uint8_t packet[FRAME_TOTAL_LEN];
    float raw_packet[RAW_DATA_SIZE];
    float processed_data[RAW_DATA_SIZE]; 

    
    // uint32_t total_time_us = 0;
    // uint32_t start_cycles, end_cycles;
    // uint32_t overhead = k_cycle_get_32();
    // overhead = k_cycle_get_32() - overhead;

    while (true)
    {
        if (k_msgq_get(&uart_msgq, &packet, K_FOREVER) == 0)
        {

            memcpy(raw_packet, &packet[2], sizeof(float) * RAW_DATA_SIZE);
            
            // start_cycles = k_cycle_get_32();
            for (int i = 0; i < RAW_DATA_SIZE; i++)
            {
                float hp_out = high_pass_filter(raw_packet[i], &filter_state);
                float abs_val = fabsf(hp_out);
                processed_data[i] = low_pass_filter(abs_val, &filter_state);

                
                if (i == (RAW_DATA_SIZE - 1))
                {
                    // update_sliding_window(processed_data[0]); 
                    
                    current_block_sum += processed_data[0];
                    current_block_count++;

                    
                    if (current_block_count >= BLOCK_SIZE)
                    {
                        
                        if (valid_blocks < BLOCK_SUMS_SIZE)
                        { 
                            window_sum += current_block_sum;
                            valid_blocks++; 
                        }
                        else
                        { 
                            window_sum += current_block_sum - block_sums[block_sum_idx];
                        }

                        
                        block_sums[block_sum_idx] = current_block_sum;
                        block_sum_idx = (block_sum_idx + 1) % 4; 

                        float mean = 0.0f;
                        mean = window_sum / WINDOW_SIZE;

                        
                        current_block_sum = 0.0f;
                        current_block_count = 0;

                        tx_buf[0] = 0xAA;
                        tx_buf[1] = 0x55;

                        
                        uint8_t *data_ptr = &tx_buf[2];
                        memcpy(data_ptr, &mean, sizeof(float));

                        
                        uint8_t checksum = 0;
                        for (int i = 0; i < 6; i++)
                        {
                            checksum += tx_buf[i];
                        }
                        tx_buf[6] = checksum;

                        
                        int ret = uart_tx(uart_dev, tx_buf, 7, SYS_FOREVER_MS);
                        if (ret != 0)
                        {
                            LOG_ERR("UART发送失败: %d", ret);
                        }
                    }
                }
            }
            k_yield();
        }
    }
}

void main(void)
{
    
    if (!device_is_ready(uart_dev))
    {
        LOG_INF("UART device not ready!\n");
        return;
    }

    // UART
    uart_callback_set(uart_dev, uart_cb, NULL);
    uart_rx_init();

    filter_state.hp_x_prev = 0.0f;
    filter_state.hp_y_prev = 0.0f;
    filter_state.lp_x_prev = 0.0f;
    filter_state.lp_y_prev = 0.0f;

    
    k_thread_create(&processing_thread, processing_stack,
                    K_THREAD_STACK_SIZEOF(processing_stack),
                    (k_thread_entry_t)processing_thread_func,
                    NULL, NULL, NULL,
                    K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

    LOG_INF("System initialized\n");
}
