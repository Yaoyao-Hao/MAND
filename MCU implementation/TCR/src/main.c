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

LOG_MODULE_REGISTER(main, LOG_LEVEL_DBG); // 
/*-------------------------------------------------------------define---------------------------------------------------------------------*/
#define UART_DEVICE_NODE DT_NODELABEL(uart0)
#define RAW_DATA_SIZE 30
#define FRAME_TOTAL_LEN (2 + 30 * 4 + 1) // 123字节
#define FILTER_ORDER 2


#define MAX_PENDING_PACKETS 10
K_MSGQ_DEFINE(uart_msgq, FRAME_TOTAL_LEN, MAX_PENDING_PACKETS, 4);

#define PROCESSING_STACK_SIZE 4096
K_THREAD_STACK_DEFINE(processing_stack, PROCESSING_STACK_SIZE); // 
/*-------------------------------------------------------------struct-----------------------------------------------------------------------------*/

struct uart_rx_context
{
    uint8_t packet[FRAME_TOTAL_LEN]; // 
    size_t recv_cnt;                 // 
    int64_t last_recv_ts;            // (ns)
    bool frame_valid;                // 
};

typedef struct
{
    float x_delay[FILTER_ORDER]; // : x[n-1], x[n-2]
    float y_delay[FILTER_ORDER]; // : y[n-1], y[n-2]
    float threshold;             // 
    uint32_t bin_counter;        // 
    uint32_t spike_count;        // 
    uint32_t bin_buffer[4];      // 
    uint8_t buffer_index;        // 
    uint8_t last_state;          // 
    uint8_t valid_blocks;        // 
    float window_sum;
} MUA_Processor;
MUA_Processor proc;
/*------------------------------------------------------------gloable variable---------------------------------------------------------------------*/
static uint8_t rx_bufs[2][FRAME_TOTAL_LEN];
static bool current_buf = 0;
static uint8_t tx_buf[FRAME_TOTAL_LEN];
static struct uart_rx_context rx_ctx;
struct uart_config config;

static struct k_thread processing_thread; // 
void processing_thread_func(void);

/*  */
const struct device *uart_dev = DEVICE_DT_GET(UART_DEVICE_NODE);

static const float b[FILTER_ORDER + 1] = {0.96365276f, -1.92730553f, 0.96365276f};
static const float a[FILTER_ORDER + 1] = {1.0000f, -1.92598397f, 0.92862709f};

/*------------------------------------------------------------function-----------------------------------------------------------------------------*/
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

        // 
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
                    /*  */
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
        // 
        uart_rx_buf_rsp(dev, rx_bufs[current_buf], FRAME_TOTAL_LEN);
        current_buf = !current_buf;

        break;
    }

    if (evt->type == UART_RX_RDY)
    {
    }
}

/*  */
static void uart_rx_init(void)
{

    uart_config_get(uart_dev, &config);
    // 
    config.baudrate = 115200;
    config.parity = UART_CFG_PARITY_NONE;
    config.stop_bits = UART_CFG_STOP_BITS_1;
    config.data_bits = UART_CFG_DATA_BITS_8;
    config.flow_ctrl = UART_CFG_FLOW_CTRL_NONE; // 
    uart_configure(uart_dev, &config);

    // 
    // static uint8_t rx_buf0[FRAME_TOTAL_LEN];
    // static uint8_t rx_buf1[FRAME_TOTAL_LEN];
    uart_rx_enable(uart_dev, rx_bufs[0], FRAME_TOTAL_LEN, 0);
    uart_rx_buf_rsp(uart_dev, rx_bufs[1], FRAME_TOTAL_LEN);
}

// 
void MUA_Init(MUA_Processor *processor, float rms)
{
    memset(processor, 0, sizeof(MUA_Processor));
    processor->threshold = -4.5 * rms;
}

// 
float filter_sample(MUA_Processor *proc, float input)
{
    // : y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]
    float output = b[0] * input + b[1] * proc->x_delay[0] + b[2] * proc->x_delay[1] - a[1] * proc->y_delay[0] - a[2] * proc->y_delay[1];

    // 
    // : x[n-2] = x[n-1], x[n-1] = x[n]
    proc->x_delay[1] = proc->x_delay[0];
    proc->x_delay[0] = input;

    // : y[n-2] = y[n-1], y[n-1] = y[n]
    proc->y_delay[1] = proc->y_delay[0];
    proc->y_delay[0] = output;

    return output;
}

void MUA_ResetFilter(MUA_Processor *proc)
{
    memset(proc->x_delay, 0, sizeof(proc->x_delay));
    memset(proc->y_delay, 0, sizeof(proc->y_delay));
    proc->last_state = 0;
}

void processing_thread_func(void)
{
    uint8_t packet[FRAME_TOTAL_LEN];
    float raw_packet[RAW_DATA_SIZE];
    // for test
    float processed_data[RAW_DATA_SIZE]; // 

    // // 
    // uint32_t total_time_us = 0;
    // uint32_t start_cycles, end_cycles;
    // uint32_t overhead = k_cycle_get_32();
    // overhead = k_cycle_get_32() - overhead;

    while (true)
    {
        if (k_msgq_get(&uart_msgq, &packet, K_FOREVER) == 0)
        {
            memcpy(raw_packet, &packet[2], sizeof(float) * RAW_DATA_SIZE);

            // // 
            // start_cycles = k_cycle_get_32();

            for (int i = 0; i < RAW_DATA_SIZE; i++)
            {
                // 1. 
                float filtered = filter_sample(&proc, raw_packet[i]);

                // 2. 
                uint8_t current_state = (filtered > proc.threshold) ? 1 : 0;
                int8_t diff = current_state - proc.last_state; // 二值化
                uint8_t spike = (diff == 1) ? 1 : 0;           //
                proc.last_state = current_state;

                // 3. 
                proc.spike_count += spike;
                proc.bin_counter++;

                // 4. 
                if (proc.bin_counter >= 1500)
                {
                    if (proc.valid_blocks < 4)
                    {
                        proc.window_sum += proc.spike_count;
                        proc.valid_blocks++;
                    }
                    else
                    {
                        proc.window_sum += proc.spike_count;
                        proc.window_sum -= proc.bin_buffer[proc.buffer_index];
                    }
                    // 
                    proc.bin_buffer[proc.buffer_index] = proc.spike_count;
                    proc.buffer_index = (proc.buffer_index + 1) % 4;

                    // 
                    float mean = 0.0f;
                    mean = proc.window_sum;

                    // 
                    proc.spike_count = 0;
                    proc.bin_counter = 0;

                    tx_buf[0] = 0xAA;
                    tx_buf[1] = 0x55;

                    // 
                    uint8_t *data_ptr = &tx_buf[2];
                    memcpy(data_ptr, &mean, sizeof(float));

                    // 
                    uint8_t checksum = 0;
                    for (int i = 0; i < 6; i++)
                    {
                        checksum += tx_buf[i];
                    }
                    tx_buf[6] = checksum;

                    /*  */
                    int ret = uart_tx(uart_dev, tx_buf, 7, SYS_FOREVER_MS);
                    if (ret != 0)
                    {
                        LOG_ERR("UART发送失败: %d", ret);
                    }
                }
            }

            

            k_yield();
        }
    }
}

void main(void)
{
    // 
    if (!device_is_ready(uart_dev))
    {
        LOG_INF("UART device not ready!\n");
        return;
    }

    // 
    uart_callback_set(uart_dev, uart_cb, NULL);
    uart_rx_init();

    MUA_Init(&proc, 21.25704080830074f);
    MUA_ResetFilter(&proc);

    // 
    k_thread_create(&processing_thread, processing_stack,
                    K_THREAD_STACK_SIZEOF(processing_stack),
                    (k_thread_entry_t)processing_thread_func,
                    NULL, NULL, NULL,
                    K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

    LOG_INF("System initialized\n");
}