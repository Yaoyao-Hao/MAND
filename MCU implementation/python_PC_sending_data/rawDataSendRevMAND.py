import numpy as np
import serial
import time
import struct
import threading

# 
PORT = 'COM5'
BAUDRATE = 115200
FRAME_SIZE = 30
HEADER = b'\xAA\x55'
SEND_INTERVAL = 0.5  # 
STOP_RECEIVER = False  # 
TOTAL_PACKETS = 200 
received_floats = []  # 

# 
received_floats = []  # 
frame_counter = 0      # 

def float32_to_bytes(data): 
    return data.astype(np.float32).tobytes()

def add_checksum(data_bytes):
    checksum = sum(data_bytes) & 0xFF
    return data_bytes + bytes([checksum])

def send_data(ser, data_chunk):
    frame = HEADER + float32_to_bytes(data_chunk)
    frame = add_checksum(frame)
    print(f"🟢 sending（{len(frame)} byte）：", frame.hex(' ', 1))
    ser.write(frame)
            
def receive_thread_func(ser):
    global received_floats
    buffer = bytearray()
    FRAME_LEN = 7
    packet_count = 0
    
    while not STOP_RECEIVER and packet_count < TOTAL_PACKETS:
        try:
            data = ser.read(7)  # 
            if data:
                buffer.extend(data)

                # 
                while True:
                    header_index = buffer.find(HEADER)
                    if header_index == -1:
                        # 
                        buffer.clear()
                        break

                    # 
                    if len(buffer) - header_index < FRAME_LEN:
                        
                        break

                    # 
                    frame = buffer[header_index : header_index + FRAME_LEN]
                    buffer = buffer[header_index + FRAME_LEN:]  # 

                    #
                    calc_checksum = sum(frame[:-1]) & 0xFF
                    recv_checksum = frame[-1]

                    if calc_checksum != recv_checksum:
                        print("❌ failed, drop frame")
                        continue

                    
                    float_bytes = frame[2:-1]  # 
                    try:
                        value = struct.unpack('<f', float_bytes)[0]  
                        received_floats.append(value)
                        packet_count += 1
                        print(f"✅ received {packet_count} data: {value:.6f}")

                    except struct.error:
                        print("❗ float error")
                        continue

        except Exception as e:
            print("receive error:", e)

    # 
    if len(received_floats) == TOTAL_PACKETS:
        np.save("MANDreceived_data0516.npy", np.array(received_floats, dtype=np.float32))
        print(f"🎯 receive complete, data in MANDreceived_data0516.npy （total {TOTAL_PACKETS} float）")              

if __name__ == "__main__":
    raw_data = np.load("raw_signal.npy")

    with serial.Serial(PORT, BAUDRATE, timeout=0.1) as ser:
        # 
        receiver_thread = threading.Thread(target=receive_thread_func, args=(ser,), daemon=True)
        receiver_thread.start()

        try:
            for i in range(0, len(raw_data), FRAME_SIZE):
                chunk = raw_data[i:i+FRAME_SIZE].astype(np.float32)
                if len(chunk) < FRAME_SIZE:
                    chunk = np.pad(chunk, (0, FRAME_SIZE - len(chunk)), mode='constant')

                send_data(ser, chunk)
                print(f"sending {i//FRAME_SIZE + 1} frame")
                time.sleep(SEND_INTERVAL)

        finally:
            #
            STOP_RECEIVER = True
            receiver_thread.join(timeout=1)
            print("sending complete, quit")
