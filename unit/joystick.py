import pygame
from gpiozero import Button
import threading
import time

class DigitalJoystick:
    def __init__(self):
        print("🎮 正在初始化物理摇杆 (数字模式)...")
        # 假设我们将 5 个方向接在以下 BCM 引脚：
        # (你可以根据你的实际接线随时修改这些数字)
        self.pin_left = 5
        self.pin_up = 6
        self.pin_down = 13
        self.pin_center = 19
        self.pin_right = 26 # 预留接口

        # 初始化 gpiozero 按键，开启防抖
        self.btn_left = Button(self.pin_left, pull_up=True, bounce_time=0.1)
        self.btn_up = Button(self.pin_up, pull_up=True, bounce_time=0.1)
        self.btn_down = Button(self.pin_down, pull_up=True, bounce_time=0.1)
        self.btn_center = Button(self.pin_center, pull_up=True, bounce_time=0.1)
        self.btn_right = Button(self.pin_right, pull_up=True, bounce_time=0.1)

        # 绑定触发事件
        self.btn_left.when_pressed = lambda: self._inject_key(pygame.K_1, "LEFT -> K_1")
        self.btn_up.when_pressed = lambda: self._inject_key(pygame.K_2, "UP -> K_2")
        self.btn_down.when_pressed = lambda: self._inject_key(pygame.K_3, "DOWN -> K_3")
        self.btn_center.when_pressed = lambda: self._inject_key(pygame.K_4, "CENTER -> K_4")
        self.btn_right.when_pressed = lambda: print("👉 物理摇杆: RIGHT (预留接口暂无映射)")

    def _inject_key(self, pygame_key, debug_msg):
        """
        核心魔法：将物理动作伪装成键盘事件，塞进 OS 的事件队列！
        """
        print(f"🕹️ 硬件触发: {debug_msg}")
        # 创建一个伪造的 KEYDOWN 事件
        fake_event = pygame.event.Event(pygame.KEYDOWN, key=pygame_key)
        # 塞入 Pygame 队列
        pygame.event.post(fake_event)

if __name__=="__main__":
    joystick=DigitalJoystick()
    