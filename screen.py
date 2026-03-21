import pygame
import time
import math
from unit.route import load_gpx_route,MapProjector
import os
import random
# import gpxpy

class BaseScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        # 黑色/白色/灰色
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GRAY = (128, 128, 128)
        self.LIGHT_GRAY = (200, 200, 200)
        self.DARK_GRAY = (64, 64, 64)

        # 红色系
        self.RED = (255, 0, 0)
        self.DARK_RED = (139, 0, 0)
        self.LIGHT_RED = (255, 100, 100)

        # 绿色系
        self.GREEN = (0, 255, 0)
        self.DARK_GREEN = (0, 100, 0)
        self.LIGHT_GREEN = (144, 238, 144)
        self.LIME = (50, 205, 50)

        # 蓝色系
        self.BLUE = (0, 0, 255)
        self.DARK_BLUE = (0, 0, 139)
        self.LIGHT_BLUE = (173, 216, 230)
        self.SKY_BLUE = (135, 206, 235)

        # 黄色/橙色
        self.YELLOW = (255, 255, 0)
        self.GOLD = (255, 215, 0)
        self.ORANGE = (255, 165, 0)
        self.DARK_ORANGE = (255, 140, 0)

        # 紫色/粉色
        self.PURPLE = (128, 0, 128)
        self.VIOLET = (238, 130, 238)
        self.PINK = (255, 192, 203)
        self.HOT_PINK = (255, 105, 180)

        # 棕色/青色
        self.BROWN = (165, 42, 42)
        self.CYAN = (0, 255, 255)
        self.TEAL = (0, 128, 128)
        self.MAGENTA = (255, 0, 255)
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
                prefix = "->  " 
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

    def init_menus(self, menus_dict, start_level='main'):
        """
        子类在初始化时调用此方法，一次性注入所有菜单数据。
        """
        self.menus = menus_dict
        if start_level in self.menus:
            self.change_menu_level(start_level)

class DesktopScreen(BaseScreen):
    """界面 1：桌面主页"""
    def __init__(self, width, height,):
        super().__init__(width, height)
        self.font_time = pygame.font.SysFont("Arial", 80, bold=True)
        self.font_date = pygame.font.SysFont("Arial", 30)    

        # --- 1. 动态读取本地图片文件 ---
        self.image_dir = '/home/ma/StarTrack/image'
        self.load_image()
        index=0
        selected_path = self.wallpaper_paths[index]
        self._load_wallpaper(selected_path)

        # --- 1. 定义多级菜单的字典 ---
        self.menus = {
            'main': [
                "1. System Info", 
                "2. Sleep Display", 
                "3. Power Off OS", 
                "4. Change Wallpaper"
            ],
            'wallpaper_menu': self.wallpaper_menu_items
        }
        self.init_menus(self.menus, start_level='main')

    def load_image(self):
        self.wallpaper_paths = []  # 初始化为实例变量
        self.wallpaper_menu_items = []  # 初始化为实例变量
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
                    self.wallpaper_menu_items.append(f"  -> {display_name}")
        else:
            print(f"⚠️ 警告: 找不到壁纸文件夹 {self.image_dir}")
            self.wallpaper_menu_items.append("  (No Images Found)")
        # 无论有没有图片，最后都必须加上返回键！
        self.wallpaper_menu_items.append("  <- Back")

    def draw(self, surface):
        surface.blit(self.bg_img, (0,0))
        
        # 绘制时间
        current_time = time.strftime("%H:%M:%S")
        current_date = time.strftime("%Y-%m-%d  %A")
        
        time_text = self.font_time.render(current_time, True, (255, 255, 255))
        date_text = self.font_date.render(current_date, True, (200, 200, 200))
        
        surface.blit(time_text, (self.width//2 - time_text.get_width()//2, self.height//3))
        surface.blit(date_text, (self.width//2 - date_text.get_width()//2, self.height//3 + 100))
        self.draw_menu(surface, 50, 50)

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
    def __init__(self, width=400, height=400):
        super().__init__(width, height)
        # 显示风格
        self.map_style = 'dark'
        # 存储当前的传感器数据
        self.current_lat = None
        self.current_lon = None
        self.heading = None
        self.compass_status=True
        
        # compass
        self.compass_radius = 180
        self.compass_cx = self.width - self.compass_radius - 40
        self.compass_cy = self.height/2 #- self.compass_radius - 20

        # map
        # --- 1. 扫描地图文件夹 ---
        self.map_dir = '/home/ma/StarTrack/map'
        # self.gpx_paths,route_menu_items=self.load_map(self.map_dir)
        self.load_map()
        # --- 2. 注入多级菜单 ---
        my_menus = {
            'main': ["1. Select Route", "2. Toggle Style", "3. Zoom In (+)", "4. Zoom Out (-)", f"5. Compass: {"ON" if self.compass_status else "OFF"}"],
            'route_menu': self.route_menu_items
        }
        self.init_menus(my_menus, start_level='main')
        # --- 3. 初始化默认地图 ---
        self.bg_surface = pygame.Surface((self.width, self.height))
        self.projector = None
        self.route_pixels = []
        
        # 如果找到了路书，默认加载第一条；否则加载一个测试用的短线防报错
        if self.gpx_paths:
            # self._load_gpx_and_project(self.gpx_paths[0])
            self.points = load_gpx_route(self.gpx_paths[0])
            self.projector = MapProjector(self.points, self.width, self.height)
            self.route_pixels = [self.projector.to_pixel(p['lat'], p['lon']) for p in self.points]
            self._draw_static_background()
        else:
            dummy_points = [{'lat': 30.25, 'lon': 120.15}, {'lat': 30.26, 'lon': 120.16}]
            self.projector = MapProjector(dummy_points, self.width, self.height)
            self.route_pixels = [self.projector.to_pixel(p['lat'], p['lon']) for p in dummy_points]
            self._draw_static_background()
    
    def load_map(self):
        self.gpx_paths=[]
        self.route_menu_items=[]
        if os.path.exists(self.map_dir):
            for file_name in sorted(os.listdir(self.map_dir)):
                if file_name.lower().endswith('.gpx'):
                    self.gpx_paths.append(os.path.join(self.map_dir, file_name))
                    # 截断过长的文件名并在前面加箭头
                    display_name = file_name[:18] + ".." if len(file_name) > 18 else file_name
                    self.route_menu_items.append(f"  -> {display_name}")
        else:
            print(f"⚠️ 找不到地图文件夹: {self.map_dir}")
            self.route_menu_items.append("  (No GPX Found)")

        self.route_menu_items.append("  <- Back") # 添加虚拟返回键

    def _draw_static_background(self):
        """根据当前的 map_style 绘制不同的背景"""
        if self.map_style == 'dark':
            bg_color, grid_color = (20, 20, 20), (0, 80, 0)
        else:
            bg_color, grid_color = (240, 235, 220), (200, 195, 180)

        self.bg_surface.fill(bg_color)
        
        # 画网格
        for i in range(0, self.width, 50):
            pygame.draw.line(self.bg_surface, grid_color, (i, 0), (i, self.height), 1)
        for i in range(0, self.height, 50):
            pygame.draw.line(self.bg_surface, grid_color, (0, i), (self.width, i), 1)
            
        # 画路线和起终点
        if self.route_pixels:
            pygame.draw.lines(self.bg_surface, self.GREEN, False, self.route_pixels, 4)
            pygame.draw.circle(self.bg_surface, self.LIGHT_GREEN, self.route_pixels[0], 6)
            pygame.draw.circle(self.bg_surface, self.LIGHT_RED, self.route_pixels[-1], 6)

    def _set_sensor_data(self, lat, lon, heading):
        """外部主程序调用此方法，将最新的 GPS 和指南针数据喂给地图"""
        self.current_lat = lat
        self.current_lon = lon
        self.heading = heading

    def update(self):
        # 内部动画逻辑可放在这里，目前数据更新依赖外部 _set_sensor_data
        lat=30.258907 
        lon=120.154046

        lat=30.259885
        lon=120.157252
        if self.compass_status is True:
            heading = random.randint(1, 360)
        else:
            heading = 0
        self._set_sensor_data(lat, lon, heading)
        # pass

    def draw(self, surface):
        """将画面画到 OS 传来的画布上"""
        # 1. 贴上静态路线图
        surface.blit(self.bg_surface, (0, 0))
        
        # 2. 如果有当前的 GPS 坐标，画出代表你自己的导航箭头
        if self.current_lat is not None and self.current_lon is not None:
            px, py = self.projector.to_pixel(self.current_lat, self.current_lon)
            self._navigation_arrow(surface, self.PINK, (px, py), 15, self.heading)

        if self.compass_status is True:
            self._hud_compass(surface, self.compass_cx, self.compass_cy, self.compass_radius, self.heading)
        self.draw_menu(surface, 50, 50)      

    def _navigation_arrow(self, surface, color, center, radius, heading):
        """画一个带有指向性的箭头"""
        angle_rad = math.radians(heading - 90)
        tip = (center[0] + radius * math.cos(angle_rad), 
               center[1] + radius * math.sin(angle_rad))
        left_wing = (center[0] + radius * 0.8 * math.cos(angle_rad + 2.5), 
                     center[1] + radius * 0.8 * math.sin(angle_rad + 2.5))
        right_wing = (center[0] + radius * 0.8 * math.cos(angle_rad - 2.5), 
                      center[1] + radius * 0.8 * math.sin(angle_rad - 2.5))
        pygame.draw.polygon(surface, color, [tip, left_wing, right_wing])

    def _hud_compass(self, surface, cx, cy, radius, heading):
        """
        绘制专业级 HUD 浮动指南针
        :param cx, cy: 指南针在屏幕上的中心坐标
        :param radius: 指南针的半径大小
        :param heading: 当前的绝对航向角 (0-360)
        """
        # 1. 绘制半透明的仪表盘底座
        dial_bg = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(dial_bg, (20, 20, 20, 200), (radius, radius), radius)
        surface.blit(dial_bg, (cx - radius, cy - radius))
        
        # 绘制外边框
        pygame.draw.circle(surface, (100, 100, 100), (cx, cy), radius, 2)
        
        # 2. 绘制旋转的刻度和字母 (N, E, S, W)
        font_labels = pygame.font.SysFont("Arial", int(radius * 0.3), bold=True)
        directions = {0: ('N', (255, 50, 50)), 90: ('E', (200, 200, 200)), 
                      180: ('S', (200, 200, 200)), 270: ('W', (200, 200, 200))}
        
        # 每隔 15 度画一个刻度
        for deg in range(0, 360, 15):
            # 核心算法：屏幕正上方是 -90 度。表盘需要根据 heading 反向旋转。
            screen_angle = math.radians(-90 + deg - heading)
            
            if deg in directions:
                # 绘制 N, E, S, W 字母
                char, color = directions[deg]
                text = font_labels.render(char, True, color)
                # 将字母往圆心缩进一点
                text_r = radius * 0.7 
                tx = cx + text_r * math.cos(screen_angle) - text.get_width() // 2
                ty = cy + text_r * math.sin(screen_angle) - text.get_height() // 2
                surface.blit(text, (tx, ty))
            else:
                # 绘制普通刻度线
                # 45度角（东北、东南等）画长线，其余画短线
                inner_r = radius * 0.85 if deg % 45 == 0 else radius * 0.92
                start_x = cx + inner_r * math.cos(screen_angle)
                start_y = cy + inner_r * math.sin(screen_angle)
                end_x = cx + radius * math.cos(screen_angle)
                end_y = cy + radius * math.sin(screen_angle)
                pygame.draw.line(surface, (150, 150, 150), (start_x, start_y), (end_x, end_y), 2)
                
        # 3. 绘制正上方的“当前航向”游标 (一个金黄色的倒三角)
        pygame.draw.polygon(surface, self.PINK, [
            (cx, cy - radius + 2),         # 顶点向下
            (cx - 8, cy - radius - 12),    # 左上
            (cx + 8, cy - radius - 12)     # 右上
        ])
        
        # 4. 在仪表盘正中央显示数字航向
        font_digital = pygame.font.SysFont("Arial", int(radius * 0.4))
        digital_text = font_digital.render(f"{int(heading)}°", True, (255, 255, 255))
        surface.blit(digital_text, (cx - digital_text.get_width() // 2, cy - digital_text.get_height() // 2))

    def on_confirm(self, index):
        """处理地图界面的菜单确认动作"""
        if self.current_menu_level == 'main':
            if index == 0:
                self.change_menu_level('route_menu') # 跳入选择路线子菜单
            elif index == 1:
                self.map_style = 'light' if self.map_style == 'dark' else 'dark'
                self._draw_static_background()
            elif index == 2:
                print("缩放功能待开发: +")
            elif index == 3:
                print("缩放功能待开发: -")
            elif index == 4:
                print("change compass statues")
                self.compass_status=not self.compass_status
                self.menus['main'][4] = f"5. Compass: {"ON" if self.compass_status else "OFF"}"

        elif self.current_menu_level == 'route_menu':
            # 判断是不是按了返回键
            if index == len(self.gpx_paths) or not self.gpx_paths:
                self.change_menu_level('main')
            else:
                # 加载选中的路书
                selected_gpx = self.gpx_paths[index]
                # self._load_gpx_and_project(selected_gpx)
                self.points = load_gpx_route(selected_gpx)
                self.projector = MapProjector(self.points, self.width, self.height)
                self.route_pixels = [self.projector.to_pixel(p['lat'], p['lon']) for p in self.points]
                self._draw_static_background()
                # 加载完成后，自动退回主菜单，保持界面清爽
                self.change_menu_level('main')

class ScreenManager:
    def __init__(self):
        pygame.init()
        # 获取显示信息
        info = pygame.display.Info()
        # 获取屏幕宽度和高度
        screen_width = info.current_w
        screen_height = info.current_h
        print(f"屏幕分辨率: {screen_width} x {screen_height}")
        self.width = screen_width
        self.height = screen_height
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
    app = ScreenManager()
    app.run()