import pygame
import time
import math
from unit.route import load_gpx_route,MapProjector
import os

class BaseScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.menu_items = []      # 存放菜单文字的列表
        self.selected_index = 0   # 当前选中的菜单项索引
        self.font_menu = pygame.font.SysFont("Arial", 24, bold=True)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and len(self.menu_items) > 0:
            menu_length = len(self.menu_items)
            if event.key == pygame.K_2: # 模拟按键 2：上一个
                # self.selected_index = (self.selected_index - 1) % len(self.menu_items)
                # self.selected_index = max(0, self.selected_index - 1)
                self.selected_index = (self.selected_index - 1) % menu_length
            elif event.key == pygame.K_3: # 模拟按键 3：下一个
                # self.selected_index = (self.selected_index + 1) % len(self.menu_items)
                # self.selected_index = min(max_index, self.selected_index + 1)
                self.selected_index = (self.selected_index + 1) % menu_length
            elif event.key == pygame.K_4: # 模拟按键 4：确认执行
                self.on_confirm(self.selected_index)
    
    def on_confirm(self, index):
        """当按下 4 键确认时触发。子类必须重写这个方法来具体干活"""
        pass
    
    def change_menu_level(self, target_level):
        """辅助函数：用于在不同菜单层级间跳转"""
        self.current_menu_level = target_level
        self.menu_items = self.menus[self.current_menu_level]
        self.selected_index = 0 # 每次切菜单，光标自动回到第一项

    def draw_menu(self, surface, start_x, start_y):
        """通用的绘制菜单模块，子类直接调用即可"""
        if not self.menu_items: return
        
        for i, item in enumerate(self.menu_items):
            # 被选中的高亮成醒目的黄色，且前面加个箭头
            if i == self.selected_index:
                color = (255, 200, 0)
                prefix = "▶  " 
            else:
                color = (150, 150, 150)
                prefix = "    "
                
            text_surf = self.font_menu.render(prefix + item, True, color)
            # 每行菜单间隔 40 像素
            surface.blit(text_surf, (start_x, start_y + i * 40))

    def update(self):
        pass

    def draw(self, surface):
        pass


class DesktopScreen(BaseScreen):
    """界面 1：桌面主页"""
    def __init__(self, width=400, height=400, bg_img="/home/ma/StarTrack/image/cloud.png"):
        super().__init__(width, height)
        self.font_time = pygame.font.SysFont("Arial", 80, bold=True)
        self.font_date = pygame.font.SysFont("Arial", 30)
        self.bg_img = pygame.image.load(bg_img)

        # --- 1. 动态读取本地图片文件 ---
        self.image_dir = '/home/ma/StarTrack/image'
        self.wallpaper_paths = []    # 存放图片的绝对路径 (后台用)
        wallpaper_menu_items = []    # 存放菜单上显示的文字 (前台用)
        
        # 扫描壁纸目录 (如果目录存在的话)
        if os.path.exists(self.image_dir):
            # 遍历文件夹中的文件，并按字母排序
            for file_name in sorted(os.listdir(self.image_dir)):
                # 只筛选常见的图片格式
                if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    # 保存绝对路径
                    self.wallpaper_paths.append(os.path.join(self.image_dir, file_name))
                    # 在菜单显示时，加上箭头，并截断过长的文件名防止越界
                    display_name = file_name[:20] + "..." if len(file_name) > 20 else file_name
                    wallpaper_menu_items.append(f"  -> {display_name}")
        else:
            print(f"⚠️ 警告: 找不到壁纸文件夹 {self.image_dir}")
            wallpaper_menu_items.append("  (No Images Found)")
        # 无论有没有图片，最后都必须加上返回键！
        wallpaper_menu_items.append("  <- Back")
        # 菜单
        self.menu_items = ["1.System Info", "2.Sleep Display", "3.Power Off OS", "4.Change the wallpaper"]
        # --- 1. 定义多级菜单的字典 ---
        self.menus = {
            'main': [
                "1. System Info", 
                "2. Sleep Display", 
                "3. Power Off OS", 
                "4. Change Wallpaper"
            ],
            'wallpaper_menu': wallpaper_menu_items
        }
        self.current_menu_level = 'main' # 记录当前在哪个层级
        self.menu_items = self.menus[self.current_menu_level]

    def draw(self, surface):
        # surface.fill((20, 30, 40)) # 深蓝灰背景
        surface.blit(self.bg_img, (0,0))
        # 如果有图片: surface.blit(self.bg_img, (0,0))
        
        # 绘制时间
        current_time = time.strftime("%H:%M:%S")
        current_date = time.strftime("%Y-%m-%d  %A")
        
        time_text = self.font_time.render(current_time, True, (255, 255, 255))
        date_text = self.font_date.render(current_date, True, (200, 200, 200))
        
        surface.blit(time_text, (self.width//2 - time_text.get_width()//2, self.height//3))
        surface.blit(date_text, (self.width//2 - date_text.get_width()//2, self.height//3 + 100))
        self.draw_menu(surface, 50, 150)

    def on_confirm(self, index):
        # 2. 根据选中的是第几个，执行对应的操作
        if self.current_menu_level == 'main':
            if index == 0:
                print("执行：显示系统运行状态和电池电量")
            elif index == 1:
                print("执行：关闭屏幕背光省电")
            elif index == 2:
                print("执行：安全关闭树莓派电源！")
            elif index == 3:
                print("进入切换壁纸页面")
                self.change_menu_level('wallpaper_menu')

        elif self.current_menu_level == 'wallpaper_menu':
            # 判断是不是按了最后面的 "<- Back" 键
            # 因为列表索引从 0 开始，如果有 3 张图，图片的 index 是 0,1,2，Back 的 index 正好是 3 (也就是图片的数量)
            if index == len(self.wallpaper_paths) or not self.wallpaper_paths:
                self.change_menu_level('main') # 返回主菜单
            else:
                # 用户选择了一张图片
                selected_path = self.wallpaper_paths[index]
                self._load_wallpaper(selected_path)

    def _load_wallpaper(self, path):
        """内部方法：加载并缩放图片"""
        try:
            print(f"正在加载壁纸: {path} ...")
            # 1. 读取原始图片
            raw_img = pygame.image.load(path).convert() # convert() 可以大幅提升 Pygame 渲染图片的帧率
            # 2. 缩放到完全贴合屏幕尺寸
            self.bg_img = pygame.transform.scale(raw_img, (self.width, self.height))
            print("✅ 壁纸切换成功！")
        except Exception as e:
            print(f"❌ 壁纸加载失败: {e}")

class MapScreen(BaseScreen):
    """界面 2：GPX 导航地图"""
    def __init__(self, width=400, height=400, path='/home/ma/StarTrack/map/westlake.gpx'):
        super().__init__(width, height)
        
        # 颜色库
        self.BLACK = (20, 20, 20)
        self.DARK_GREEN = (0, 80, 0)
        self.ROUTE_COLOR = (50, 150, 255)
        self.START_COLOR = (0, 255, 0)
        self.END_COLOR = (255, 50, 50)
        self.MY_COLOR = (255, 200, 0) 
        
        # 存储当前的传感器数据
        self.current_lat = None
        self.current_lon = None
        self.heading = 0
        self.route_points = load_gpx_route(path)
        # 如果没有传入路线数据，生成一条模拟线防止程序崩溃
        if not self.route_points:
            print("警告：没有路线数据，使用测试路线。")
            self.route_points = [{'lat': 30.25, 'lon': 120.15}, {'lat': 30.26, 'lon': 120.16}]

        # 初始化投影器并缓存路线像素点
        self.projector = MapProjector(self.route_points, width, height)
        self.route_pixels = [self.projector.to_pixel(p['lat'], p['lon']) for p in self.route_points]
        
        # 预先绘制静态背景 Surface，极大提升帧率
        self.bg_surface = pygame.Surface((self.width, self.height))
        self._draw_static_background()

    def _draw_static_background(self):
        """绘制不会改变的背景和路线"""
        self.bg_surface.fill(self.BLACK)
        for i in range(0, self.width, 50):
            pygame.draw.line(self.bg_surface, self.DARK_GREEN, (i, 0), (i, self.height), 1)
        for i in range(0, self.height, 50):
            pygame.draw.line(self.bg_surface, self.DARK_GREEN, (0, i), (self.width, i), 1)
            
        pygame.draw.lines(self.bg_surface, self.ROUTE_COLOR, False, self.route_pixels, 4)
        pygame.draw.circle(self.bg_surface, self.START_COLOR, self.route_pixels[0], 6)
        pygame.draw.circle(self.bg_surface, self.END_COLOR, self.route_pixels[-1], 6)

    def _set_sensor_data(self, lat, lon, heading):
        """外部主程序调用此方法，将最新的 GPS 和指南针数据喂给地图"""
        self.current_lat = lat
        self.current_lon = lon
        self.heading = heading

    def update(self):
        # 内部动画逻辑可放在这里，目前数据更新依赖外部 _set_sensor_data
        pass

    def draw(self, surface):
        """将画面画到 OS 传来的画布上"""
        # 1. 贴上静态路线图
        surface.blit(self.bg_surface, (0, 0))
        
        # 2. 如果有当前的 GPS 坐标，画出代表你自己的导航箭头
        if self.current_lat is not None and self.current_lon is not None:
            px, py = self.projector.to_pixel(self.current_lat, self.current_lon)
            self._draw_navigation_arrow(surface, self.MY_COLOR, (px, py), 15, self.heading)

    def _draw_navigation_arrow(self, surface, color, center, radius, heading):
        """画一个带有指向性的箭头"""
        angle_rad = math.radians(heading - 90)
        tip = (center[0] + radius * math.cos(angle_rad), 
               center[1] + radius * math.sin(angle_rad))
        left_wing = (center[0] + radius * 0.8 * math.cos(angle_rad + 2.5), 
                     center[1] + radius * 0.8 * math.sin(angle_rad + 2.5))
        right_wing = (center[0] + radius * 0.8 * math.cos(angle_rad - 2.5), 
                      center[1] + radius * 0.8 * math.sin(angle_rad - 2.5))
        pygame.draw.polygon(surface, color, [tip, left_wing, right_wing])


class ScreenManager:
    def __init__(self, width, height):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("StarTrack OS")
        self.clock = pygame.time.Clock()

        self.screen_order = ['desktop', 'map']
        self.current_index = 0
        self.current_screen_name = self.screen_order[self.current_index]
        # 初始化所有界面
        self.screens = {
            'desktop': DesktopScreen(self.width, self.height),
            'map': MapScreen(self.width, self.height),
            # 'compass': CompassScreen(self.width, self.height)
        }
                
        # 底部导航栏高度
        self.nav_height = 60

    def run(self):
        running = True
        while running:
            current_screen = self.screens[self.current_screen_name]

            # 1. 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    # 【系统级拦截】：按键 1 (轮回切换界面)
                    if event.key == pygame.K_1:
                        self.current_index = (self.current_index + 1) % len(self.screen_order)
                        self.current_screen_name = self.screen_order[self.current_index]
                        print(f"切换至页面: {self.current_screen_name.upper()}")
                        
                    # 【放行】：如果按的不是 1，统统扔给当前界面的 handle_event 去处理
                    else:
                        current_screen.handle_event(event)

            # 2. 更新逻辑 (读取传感器等)
            current_screen.update()

            # 3. 绘制画面
            self.screen.fill((0, 0, 0)) # 清屏
            
            # 创建一个稍微小一点的画板给子界面，留出底部导航栏的位置
            view_surface = pygame.Surface((self.width, self.height - self.nav_height))
            current_screen.draw(view_surface)
            self.screen.blit(view_surface, (0, 0))

            # 4. 绘制全局的底部导航栏
            self._draw_nav_bar()

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()

    def _draw_nav_bar(self):
        """画底部的状态/导航栏"""
        nav_rect = pygame.Rect(0, self.height - self.nav_height, self.width, self.nav_height)
        pygame.draw.rect(self.screen, (50, 50, 50), nav_rect)
        
        font = pygame.font.SysFont("Arial", 20)
        nav_text = font.render(f"1:Desktop | 2:Map | 3:Compass  -- Current: {self.current_screen_name.upper()}", True, (255, 255, 0))
        self.screen.blit(nav_text, (20, self.height - self.nav_height + 20))

if __name__ == "__main__":
    # 假设你的树莓派屏幕是 800x600
    app = ScreenManager(1381,776)
    app.run()