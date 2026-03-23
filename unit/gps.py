import serial
import pynmea2
import time

class GPSModule:
    def __init__(self, port='/dev/ttyS0', baudrate=9600):
        """
        初始化 GPS 模块
        :param port: 树莓派的串口设备名 (如果是 USB 模块，可能是 /dev/ttyUSB0)
            ls /dev/ttyUSB*
            ls -l /dev/serial*
        :param baudrate: ATGM336H 的默认波特率通常是 9600
        """
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
        except Exception as e:
            raise RuntimeError(f"无法打开串口 {port}，请检查接线和权限。错误信息: {e}")

    def get_location(self):
        """
        读取并解析 GPS 数据
        :return: (经度, 纬度, 海拔, 卫星数量) 或 None
        """
        try:
            # 读一行数据并解码
            line = self.serial_port.readline().decode('ascii', errors='replace').strip()
            
            # ATGM336H 输出包含 GNGGA (定位数据) 或 GNRMC (推荐最小数据)
            if line.startswith('$GNGGA') or line.startswith('$GPGGA'):
                msg = pynmea2.parse(line)
                
                # 检查是否成功定位 (GPS质量指示：0为未定位，1为SPS定位，2为DGPS等)
                if msg.gps_qual > 0:
                    latitude = msg.latitude      # 纬度 (十进制)
                    longitude = msg.longitude    # 经度 (十进制)
                    altitude = msg.altitude      # 海拔高度 (米)
                    num_sats = msg.num_sats      # 参与定位的卫星数量
                    
                    return {
                        "lat": latitude,
                        "lon": longitude,
                        "alt": altitude,
                        "sats": num_sats,
                        "status":"3D Fix"
                    }
                else:
                    return {
                        "lat": None,
                        "lon": None,
                        "alt": None,
                        "sats": 0,
                        "status": "search star"}
                    
        except pynmea2.ParseError:
            # 串口刚启动时可能会读到半截字符串，忽略即可
            pass
        except Exception as e:
            pass
            
        return None

# 测试代码
if __name__ == "__main__":
    try:
        # 注意：树莓派4B的硬件引脚串口通常映射为 /dev/ttyS0 或 /dev/serial0
        print("正在初始化 GPS 模块...")
        my_gps = GPSModule(port='/dev/ttyS0', baudrate=9600)
        print("GPS 启动成功，开始读取数据...")
        
        while True:
            data = my_gps.get_location()
            if data:
                if "status" in data:
                    print(f"[{time.strftime('%H:%M:%S')}] {data['status']} (请确保天线在室外且无遮挡)")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] 定位成功！")
                    print(f"  纬度: {data['lat']:.6f}°")
                    print(f"  经度: {data['lon']:.6f}°")
                    print(f"  海拔: {data['alt']} 米")
                    print(f"  可用卫星: {data['sats']} 颗\n")
            
            time.sleep(0.1) # 高频读取避免串口缓冲区堆积
            
    except KeyboardInterrupt:
        print("\nGPS 测试结束。")