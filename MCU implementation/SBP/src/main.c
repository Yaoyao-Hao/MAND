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

#define UART_DEVICE_NODE DT_NODELABEL(uart0)
#define RAW_DATA_SIZE 30
#define DOWN_SAMPLE_RATE 30
#define WINDOW_SIZE 400
#define STEP_SIZE 100
#define BLOCK_SIZE 100                   // 
#define BLOCK_SUMS_SIZE 4                // 
#define FRAME_TOTAL_LEN (2 + 30 * 4 + 1) // 

// 
static const float b[] = {0.00486164f, 0.0f, -0.00972329f, 0.0f, 0.00486164f};
static const float a[] = {1.0000f, -3.76832677f, 5.35202538f, -3.39629194f, 0.81274967f};

// 
static float x_history[4] = {0}; // 
static float y_history[4] = {0}; // 

// 
#define DOWNSAMPLE_INTERVAL 15         // 
static float current_block_sum = 0.0f; // 
static int current_block_count = 0;    // 

static float block_sums[BLOCK_SUMS_SIZE] = {0};
static int block_sum_idx = 0;
static float window_sum = 0.0f;
static int valid_blocks = 0;

static float window_sums[5] = {0};
static int window_sum_idx = 0;

struct uart_rx_context
{
    uint8_t packet[FRAME_TOTAL_LEN]; // 
    size_t recv_cnt;                 // 
    int64_t last_recv_ts;            // 
    bool frame_valid;                // 
};

static uint8_t rx_bufs[2][FRAME_TOTAL_LEN];
static bool current_buf = 0;
static uint8_t tx_buf[FRAME_TOTAL_LEN];

static struct uart_rx_context rx_ctx;
struct uart_config config;

#define MAX_PENDING_PACKETS 10
K_MSGQ_DEFINE(uart_msgq, FRAME_TOTAL_LEN, MAX_PENDING_PACKETS, 4);

#define PROCESSING_STACK_SIZE 4096
K_THREAD_STACK_DEFINE(processing_stack, PROCESSING_STACK_SIZE); // 

static struct k_thread processing_thread; // 
void processing_thread_func(void);

const struct device *uart_dev = DEVICE_DT_GET(UART_DEVICE_NODE);

float iir_filter(float x_val)
{
    float yn = b[0] * x_val +
               b[1] * x_history[0] +
               b[2] * x_history[1] +
               b[3] * x_history[2] +
               b[4] * x_history[3] -
               a[1] * y_history[0] -
               a[2] * y_history[1] -
               a[3] * y_history[2] -
               a[4] * y_history[3];

    for (int i = 3; i > 0; i--)
    {
        x_history[i] = x_history[i - 1];
        y_history[i] = y_history[i - 1];
    }
    x_history[0] = x_val;
    y_history[0] = yn;

    return fabsf(yn); // 
}

static bool verify_checksum(const uint8_t *data, size_t len)
{
    uint8_t sum = 0;
    for (size_t i = 0; i < len - 1; i++)
    { // 
        sum += data[i];
    }
    return (sum == data[len - 1]);
}

static void send_debug_info(const struct device *uart, uint32_t length)
{
    uint8_t debug_buf[20];
    int len = snprintf(debug_buf, sizeof(debug_buf), "RX Len: %u\r\n", length);

    for (int i = 0; i < len; i++)
    {
        uart_poll_out(uart, debug_buf[i]);
    }
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
    config.flow_ctrl = UART_CFG_FLOW_CTRL_NONE; // 
    uart_configure(uart_dev, &config);

    uart_rx_enable(uart_dev, rx_bufs[0], FRAME_TOTAL_LEN, 0);
    uart_rx_buf_rsp(uart_dev, rx_bufs[1], FRAME_TOTAL_LEN);
}

static void send_float_sample(const struct device *uart, float sample)
{
    uint8_t buffer[4]; // 

    memcpy(buffer, &sample, sizeof(float));

    uart_tx(uart, buffer, sizeof(buffer), SYS_FOREVER_MS);
}

void processing_thread_func(void)
{
    uint8_t packet[FRAME_TOTAL_LEN];
    float raw_packet[RAW_DATA_SIZE];
    float processed_data[RAW_DATA_SIZE]; // 

    while (true)
    {
        if (k_msgq_get(&uart_msgq, &packet, K_FOREVER) == 0)
        {

            memcpy(raw_packet, &packet[2], sizeof(float) * RAW_DATA_SIZE);

            // start_cycles = k_cycle_get_32();
            for (int i = 0; i < RAW_DATA_SIZE; i++)
            {
                processed_data[i] = iir_filter(raw_packet[i]);
                processed_data[i] = fabsf(processed_data[i]);

                if (i % DOWNSAMPLE_INTERVAL == 0)
                {
                    current_block_sum += processed_data[i];
                    current_block_count++;

                    if (current_block_count >= BLOCK_SIZE)
                    {
                        if (valid_blocks < BLOCK_SUMS_SIZE)
                        { 
                            window_sum += current_block_sum;
                            valid_blocks++; 
                        }
                        else
                        { // 
                            window_sum += current_block_sum - block_sums[block_sum_idx];
                        }

                        block_sums[block_sum_idx] = current_block_sum;
                        block_sum_idx = (block_sum_idx + 1) % 4; // 

                        float mean = 0.0f;
                        mean = window_sum / WINDOW_SIZE;

                        // 
                        current_block_sum = 0.0f;
                        current_block_count = 0;

                        tx_buf[0] = 0xAA;
                        tx_buf[1] = 0x55;

                        // 
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
                            LOG_ERR("UART fialed: %d", ret);
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

    uart_callback_set(uart_dev, uart_cb, NULL);
    uart_rx_init();

    k_thread_create(&processing_thread, processing_stack,
                    K_THREAD_STACK_SIZEOF(processing_stack),
                    (k_thread_entry_t)processing_thread_func,
                    NULL, NULL, NULL,
                    K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

    LOG_INF("System initialized\n");
}
