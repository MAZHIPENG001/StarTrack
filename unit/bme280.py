import smbus2
import bme280

class EnvironmentSensor:
    def __init__(self, port=1, address=0x76):
        """
        初始化 BME280 环境传感器
        :param port: I2C 端口号 (树莓派默认是 1)
        :param address: BME280 的 I2C 地址 (一般是 0x76 或 0x77)
        """
        self.port = port
        self.address = address
        try:
            self.bus = smbus2.SMBus(self.port)
            # 加载传感器的出厂校准参数（BME280 必须的一步）
            self.calibration_params = bme280.load_calibration_params(self.bus, self.address)
            
            # 国际标准海平面气压 (hPa / 百帕)。
            # 极客提示：在专业的户外表里，这个值可以在出发前手动校准，以获得最精确的绝对海拔。
            self.sea_level_pressure = 1013.25 
            self.is_connected = True
            print("✅ BME280 环境传感器初始化成功！")
        except Exception as e:
            print(f"❌ BME280 初始化失败，请检查接线或 I2C 地址 (0x76/0x77): {e}")
            self.is_connected = False

    def get_data(self):
        if not self.is_connected:
            return None
            
        try:
            # 读取原始数据
            data = bme280.sample(self.bus, self.address, self.calibration_params)
            
            # ⭐️ 核心航电算法：根据气压计算海拔高度 (Barometric Altitude)
            # 公式: h = 44330 * [1 - (P/P0)^(1/5.255)]
            altitude = 44330.0 * (1.0 - (data.pressure / self.sea_level_pressure)**0.1903)
            
            return {
                "temp": round(data.temperature, 1),      # 摄氏度
                "humidity": round(data.humidity, 1),     # 相对湿度 %
                "pressure": round(data.pressure, 1),     # 气压 hPa
                "alt": round(altitude, 1)                # 气压海拔 (米)
            }
        except Exception as e:
            print(f"⚠️ 读取 BME280 数据失败: {e}")
            return None

# 单独测试脚本
if __name__ == "__main__":
    import time
    sensor = EnvironmentSensor()
    while True:
        data = sensor.get_data()
        if data:
            print(f"温度: {data['temp']}°C | 湿度: {data['humidity']}% | 气压: {data['pressure']}hPa | 气压海拔: {data['alt']}m")
        time.sleep(1)