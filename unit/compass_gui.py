import math
import pygame

class CompassGUI:
    def __init__(self, width=400, height=400, title="Compass"):
        """
        初始化指南针图形界面
        """
        # 初始化 Pygame
        pygame.init()
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(title)
        
        # 预定义颜色
        self.BLACK = (30, 30, 30)
        self.WHITE = (255, 255, 255)
        self.RED = (220, 50, 50)
        self.GRAY = (150, 150, 150)
        
        # 预定义字体
        self.font = pygame.font.SysFont("Arial", 24)
        self.large_font = pygame.font.SysFont("Arial", 48, bold=True)
        
        # 计算中心点和半径
        self.center = (self.width // 2, self.height // 2)
        self.radius = min(self.width, self.height) // 2 - 50
        
        # 用于控制帧率
        self.clock = pygame.time.Clock()

    def draw(self, heading):
        """
        根据传入的航向角绘制每一帧画面
        :param heading: 航向角 (0-360度)
        """
        self.screen.fill(self.BLACK)
        
        # 1. 画表盘外圈
        pygame.draw.circle(self.screen, self.WHITE, self.center, self.radius, 3)
        
        # 2. 画东南西北方向标识
        self._draw_text("N", self.RED, (self.center[0], self.center[1] - self.radius - 20))
        self._draw_text("E", self.WHITE, (self.center[0] + self.radius + 20, self.center[1]))
        self._draw_text("S", self.WHITE, (self.center[0], self.center[1] + self.radius + 20))
        self._draw_text("W", self.WHITE, (self.center[0] - self.radius - 20, self.center[1]))

        # 3. 显示具体的数字角度
        deg_text = self.large_font.render(f"{heading:.1f}°", True, self.WHITE)
        self.screen.blit(deg_text, (0, 0))

        # 4. 计算并绘制指针
        # Pygame Y 轴向下，角度映射需要微调 (-90度让0度指向正上方)
        angle_rad = math.radians(heading - 90) 
        
        # 北极指针 (红)
        north_x = self.center[0] + int(self.radius * 0.8 * math.cos(angle_rad))
        north_y = self.center[1] + int(self.radius * 0.8 * math.sin(angle_rad))
        pygame.draw.line(self.screen, self.RED, self.center, (north_x, north_y), 8)
        
        # 南极指针 (灰)
        south_x = self.center[0] - int(self.radius * 0.8 * math.cos(angle_rad))
        south_y = self.center[1] - int(self.radius * 0.8 * math.sin(angle_rad))
        pygame.draw.line(self.screen, self.GRAY, self.center, (south_x, south_y), 8)
        
        # 画中心轴承点
        pygame.draw.circle(self.screen, self.WHITE, self.center, 10)
        
        # 更新屏幕显示
        pygame.display.flip()

    def _draw_text(self, text, color, position):
        """辅助方法：在指定中心点绘制文字"""
        text_surface = self.font.render(text, True, color)
        rect = text_surface.get_rect(center=position)
        self.screen.blit(text_surface, rect)

    def check_quit(self):
        """
        检查用户是否点击了关闭窗口的 X 按钮
        :return: 如果点击了退出返回 True，否则返回 False
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
        return False

    def close(self):
        """清理并关闭 Pygame"""
        pygame.quit()

def main():
    import random
    # 实例化图形界面模块
    gui = CompassGUI(width=500, height=500, title="Compass")
    print("图形界面启动...")

    # 主循环
    running = True
    while running:
        # 检查是否关闭了窗口
        if gui.check_quit():
            running = False
            continue
            
        # # 从传感器获取最新角度
        # heading = sensor.get_heading()
        heading = random.randint(1, 360)
        # 将角度传给 GUI 进行绘制
        gui.draw(heading)
        
        # 控制帧率 (限制在 30 帧/秒，避免占用过多 CPU)
        gui.clock.tick(10)
        heading=heading+1
    # 4. 退出清理
    gui.close()
    print("程序已安全退出。")

if __name__ == "__main__":
    main()