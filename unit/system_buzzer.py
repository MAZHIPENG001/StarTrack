from gpiozero import Buzzer
import time

class SystemBuzzer:
    def __init__(self, pin=17):
        """
        初始化系统蜂鸣器
        :param pin: BCM 引脚号，默认接 BCM 17
        """
        try:
            self.buzzer = Buzzer(pin)
            self.is_connected = True
            print(f"🔔 有源蜂鸣器初始化成功 (绑定引脚 BCM {pin})")
        except Exception as e:
            print(f"❌ 蜂鸣器初始化失败: {e}")
            self.is_connected = False

    def click(self):
        """按键反馈：极其短促的单次滴声 (不阻塞主线程)"""
        if self.is_connected:
            # on_time=0.03秒，非常干脆利落
            self.buzzer.beep(on_time=0.03, off_time=0, n=1, background=True)

    def warning_alarm(self):
        """偏航警报：急促的双音警报"""
        if self.is_connected:
            # 响0.1秒，停0.1秒，循环2次
            self.buzzer.beep(on_time=0.1, off_time=0.1, n=2, background=True)

# 独立测试代码
if __name__ == "__main__":
    bz = SystemBuzzer()
    print("测试按键音...")
    bz.click()
    time.sleep(1)
    print("测试警报音...")
    bz.warning_alarm()
    time.sleep(1)