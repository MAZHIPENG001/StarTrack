import math
from lsm303d import LSM303D

class Compass:
    def __init__(self, i2c_address=0x1E, filter_size=5):
        """
        初始化指南针模块
        :param i2c_address: 传感器的 I2C 地址，通常是 0x1D(SA0---3.3v) 或 0x1E(*SA0---GND)
        :param filter_size: 移动平均滤波的采样次数，越大读数越平滑，但响应越慢
        """
        try:
            self.lsm = LSM303D(i2c_address)
        except Exception as e:
            raise RuntimeError(f"初始化 LSM303D 失败，请检查接线和 I2C 地址: {e}")
        
        # 用于存放历史读数，进行平滑滤波
        self.history_x = []
        self.history_y = []
        self.filter_size = filter_size

    def _get_smoothed_mag(self):
        """获取经过平滑处理的磁力计 X 和 Y 数据 (内部方法)"""
        mag_x, mag_y, mag_z = self.lsm.magnetometer()
        
        self.history_x.append(mag_x)
        self.history_y.append(mag_y)
        
        # 保持列表长度不超过 filter_size
        if len(self.history_x) > self.filter_size:
            self.history_x.pop(0)
            self.history_y.pop(0)
            
        # 计算平均值
        avg_x = sum(self.history_x) / len(self.history_x)
        avg_y = sum(self.history_y) / len(self.history_y)
        
        return avg_x, avg_y

    def get_heading(self):
        """
        获取当前的航向角 (0-360度)
        """
        # 使用平滑后的数据计算
        x, y = self._get_smoothed_mag()
        
        heading_rad = math.atan2(y, x)
        heading_deg = math.degrees(heading_rad)
        
        if heading_deg < 0:
            heading_deg += 360
            
        return heading_deg

    def get_direction_string(self, heading=None):
        """
        获取当前方向的文本描述 (如: 北, 东南)
        """
        if heading is None:
            heading = self.get_heading()
            
        directions = ["北 (N)", "东北 (NE)", "东 (E)", "东南 (SE)", 
                      "南 (S)", "西南 (SW)", "西 (W)", "西北 (NW)"]
        index = round(heading / 45) % 8
        return directions[index]
        
    def read_all(self):
        """
        一次性获取角度和方向
        :return: (角度, 方向字符串) 的元组
        """
        heading = self.get_heading()
        direction = self.get_direction_string(heading)
        return heading, direction

def main():
    # 1. 实例化指南针对象
    # 如果你的地址是 0x1E，可以写成 my_compass = Compass(i2c_address=0x1E)
    try:
        my_compass = Compass(i2c_address=0x1E)
        print("指南针模块加载成功！")
    except RuntimeError as e:
        print(e)
        return

    print("按 Ctrl+C 退出...")
    
    # 2. 在主循环中轻松调用
    try:
        while True:
            # 直接调用模块的 read_all 方法，同时获取角度和方向
            heading, direction = my_compass.read_all()
            
            # 或者你也可以分开调用：
            # heading = my_compass.get_heading()
            # direction = my_compass.get_direction_string(heading)
            
            print(f"当前角度: {heading:05.1f}°  -->  {direction}")
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        print("\n程序结束。")

if __name__ == "__main__":
    import time
    main()