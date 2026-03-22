import math
from lsm303d import LSM303D
import sys
sys.path.append('/home/ma/StarTrack')
from cfg.config_manager import global_config as cfg
import time
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

        self.offset_x = cfg.get('mag_offset_x', 0.0)
        self.offset_y = cfg.get('mag_offset_y', 0.0)

    def _get_smoothed_mag(self):
        """获取经过平滑处理的磁力计 X 和 Y 数据 (内部方法)"""
        mag_x, mag_y, mag_z = self.lsm.magnetometer()
        
        # ⭐️ 核心：在进行任何滤波和计算之前，先把圆心拉回原点！
        mag_x = mag_x - self.offset_x
        mag_y = mag_y - self.offset_y

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
    
    # ==========================================
    # ⭐️ 内置全自动校准方法
    # ==========================================
    def calibrate(self, duration=30):
        """
        执行磁力计硬铁校准（画8字），并自动应用和保存。
        :param duration: 校准采样的持续时间（秒）
        """
        print("\n=======================================")
        print("🧭 磁力计硬铁校准程序启动！")
        print("=======================================")
        print("倒计时 3 秒后开始记录数据...")
        time.sleep(3)
        print("\n👉 现在！请拿着你的整个设备，")
        print("在空中缓慢地画巨大的 '8' 字形，并且不断翻转它的各种姿态。")
        print(f"校准将持续 {duration} 秒...\n")

        # 初始化极值
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        start_time = time.time()
        
        while time.time() - start_time < duration:
            # 注意：校准时必须读取最底层的原始数据，不能用 _get_smoothed_mag()
            mag_x, mag_y, mag_z = self.lsm.magnetometer()
            
            # 记录这段时间内的最大和最小值
            min_x = min(min_x, mag_x)
            max_x = max(max_x, mag_x)
            min_y = min(min_y, mag_y)
            max_y = max(max_y, mag_y)
            
            # 打印简单的进度条 (终端显示用)
            elapsed = int(time.time() - start_time)
            print(f"\r采集进度: [{'#' * elapsed}{'.' * (duration - elapsed)}] {elapsed}/{duration}s", end="")
            time.sleep(0.05)

        # 1. 计算出真正的圆心偏移量
        new_offset_x = (max_x + min_x) / 2
        new_offset_y = (max_y + min_y) / 2

        print("\n\n✅ 校准完成！")
        print(f"测得新偏移量 -> X: {new_offset_x:.2f}, Y: {new_offset_y:.2f}")

        # 2. 立即更新当前内存中的偏移量，让设备立刻变准
        self.offset_x = new_offset_x
        self.offset_y = new_offset_y

        # 3. 极其关键：清空滤波器的历史数据！
        # 因为里面的老数据带有旧的误差，不清空会导致指针突然漂移
        self.history_x.clear()
        self.history_y.clear()

        # 4. 召唤管家，把新数据永久写进 JSON 文件
        try:
            cfg.set('mag_offset_x', round(new_offset_x, 2))
            cfg.set('mag_offset_y', round(new_offset_y, 2))
            print("🎉 校准数据已自动保存至系统配置 sys_config.json！")
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")

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