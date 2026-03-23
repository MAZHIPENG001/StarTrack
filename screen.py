import pygame
import time
import math
import json
import os
import random
import gpxpy

from cfg.config_manager import global_config as cfg
from unit.wifi_locator import WifiLocator
from unit.joystick import DigitalJoystick
from unit.compass import Compass
from unit.gps import GPSModule
from unit.route import load_gpx_route,MapProjector

def calc_distance(lat1, lon1, lat2, lon2):
    """使用 Haversine 公式计算地球上两点间的距离（单位：米）"""
    R = 6371000  # 地球半径
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def calc_bearing(lat1, lon1, lat2, lon2):
    """计算从点 1 指向点 2 的绝对方位角（0-360度，0代表正北）"""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    initial_bearing = math.atan2(x, y)
    return (math.degrees(initial_bearing) + 360) % 360

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
    
    def change_menu_level(self, target_level):
        """辅助函数：用于在不同菜单层级间跳转"""
        self.current_menu_level = target_level
        self.menu_items = self.menus[self.current_menu_level]
        self.selected_index = 0 # 每次切菜单，光标自动回到第一项

    def feed_data(self, **sensor_data):
        """
        核心升级：统一的数据接收接口！
        主程序把所有硬件数据像自助餐一样摆在这里，子类界面按需拿取。
        """
        pass

class DesktopScreen(BaseScreen):
    """界面 1：桌面主页"""
    def __init__(self, width, height,):
        super().__init__(width, height)
        self.font_time = pygame.font.SysFont("Arial", 80, bold=True)
        self.font_date = pygame.font.SysFont("Arial", 30)    

        # --- 1. 动态读取本地图片文件 ---
        self.image_dir = './wallpaper'
        self.load_image()
        index=0
        self.selected_path = self.wallpaper_paths[index]
        # self.selected_path=None
        self._load_wallpaper(self.selected_path)

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
                self.selected_path = self.wallpaper_paths[index]
                self._load_wallpaper(self.selected_path)

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
        self.lat = None
        self.lon = None
        self.heading = None
        self.compass_status=True
        
        # compass
        self.compass_radius = 180
        self.compass_cx = self.width - self.compass_radius - 40
        self.compass_cy = self.height/2 #- self.compass_radius - 20

        # Zoom
        # --- 地图视图状态 ---
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.pan_step = 80 # 每次平移移动 80 个像素

        # map
        # --- 0. 初始化地图参数 ---
        self.projector = None
        self.route_pixels = []
        # --- 1. 扫描地图文件夹 ---
        self.map_dir = './map'
        # self.gpx_paths,route_menu_items=self.load_map(self.map_dir)
        self.load_map()
        # --- 2. 注入多级菜单 ---
        my_menus = {
            'main': [
                "1. Select Route", 
                "2. Toggle Style", 
                "3. Zoom(+-)",  
                f"4. Compass: {"ON" if self.compass_status else "OFF"}",
                '5. Compass calibrate'
                ],
            'route_menu': self.route_menu_items,
            'zoom':[
                '1. Select area',
                '2. Zoom In ++',
                '3. Zoom Out --',
                '4. wifi location',
                '5. <- back'
                ],
            'select_area':[
                '1. up',
                '2. down',
                '3. left',
                '4. right',
                '5. back to my location',
                '6. back to map default',
                # '6. set all default',
                '7. <-back'
            ]
        }
        self.init_menus(my_menus, start_level='main')
        # --- 3. 初始化背景 ---
        self.bg_surface = pygame.Surface((self.width, self.height))
        
        # 如果找到了路书，默认加载第一条；否则加载一个测试用的短线防报错
        if self.gpx_paths:
            self._load_gpx_and_project(self.gpx_paths[0])
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

    def feed_data(self, **sensor_data):
        # 使用 .get() 方法，如果主程序没传这个数据，就默认返回 None 或 0，不会报错
        self.lat = sensor_data.get('lat')
        self.lon = sensor_data.get('lon')
        self.heading = sensor_data.get('heading', 0)
        
        # 新增接收 GPS 状态数据
        self.alt = sensor_data.get('alt', 0)
        self.sats = sensor_data.get('sats', 0)
        self.gps_status = sensor_data.get('gps_status', 'Unknown')
    
    def draw(self, surface):
        """将画面画到 OS 传来的画布上"""
        # 1. 贴上静态路线图
        surface.blit(self.bg_surface, (0, 0))
        
        # 2. 如果有当前的 GPS 坐标，画出代表你自己的导航箭头
        if self.lat is not None and self.lon is not None:
            px, py = self.projector.to_pixel(self.lat, self.lon)
            self._navigation_arrow(surface, self.PINK, (px, py), 15, self.heading)

        if self.compass_status is True:
            self._hud_compass(surface, self.compass_cx, self.compass_cy, self.compass_radius, self.heading)
        self._hud_gps(surface)
        self.draw_menu(surface, 50, 50)
        self._hud_pointer(surface)
    
    def _hud_pointer(self,surface):
        # ==========================================
        # ⭐️ 新增：绘制偏航导航箭头 (Off-Course Pointer)
        # ==========================================
        dist_to_track, pointer_angle = self._calculate_navigation()
        
        if dist_to_track is not None and pointer_angle is not None:
            # 只有当偏离路线超过 10 米时，才显示警告箭头，否则说明走得很好
            if dist_to_track > 10:
                # 设定箭头在屏幕上的中心位置 (屏幕顶部居中)
                arrow_center_x = self.width // 2
                arrow_center_y = self.height // 2
                
                # 定义一个基础箭头形状的多边形坐标 (指向上方)
                # 形状类似于战斗机: 尖头, 左翼, 尾凹, 右翼
                base_arrow = [(0, -30), (-20, 20), (0, 10), (20, 20)]
                
                rotated_arrow = []
                # 注意：Pygame 的旋转是逆时针的，所以我们要取负数
                rad = math.radians(-pointer_angle) 
                cos_a = math.cos(rad)
                sin_a = math.sin(rad)
                
                for x, y in base_arrow:
                    # 矩阵旋转公式
                    rx = x * cos_a - y * sin_a
                    ry = x * sin_a + y * cos_a
                    rotated_arrow.append((arrow_center_x + rx, arrow_center_y + ry))
                
                # 画一个发光的红色外边框
                pygame.draw.polygon(surface, (255, 50, 50), rotated_arrow, 4)
                # 画一个深红色的内部填充
                pygame.draw.polygon(surface, (150, 0, 0), rotated_arrow, 0)
                
                # 在箭头下方显示距离偏航多远
                font_warn = pygame.font.SysFont("Arial", 18, bold=True)
                txt_dist = font_warn.render(f"OFF COURSE: {int(dist_to_track)}m", True, (255, 100, 100))
                dist_rect = txt_dist.get_rect(center=(arrow_center_x, arrow_center_y + 45))
                surface.blit(txt_dist, dist_rect)
    
    def _hud_gps(self,surface):
        # ==========================================
        # ⭐️ 绘制 GPS 状态监控面板
        # ==========================================
        panel_width = 180
        panel_height = 80
        
        # 📍 在这里修改基础坐标，整个面板就会跟着走！
        # ------------------------------------------------
        # 方案 A：左上角 (默认)
        # base_x = 10
        # base_y = 10
        
        # 方案 B：左下角 (比如你想把它挪到最下面)
        # base_x = 10
        # base_y = self.height - panel_height - 10
        
        # 方案 C：顶部居中 
        base_x = (self.width - panel_width) // 2
        base_y = 10
        # ------------------------------------------------

        # 1. 绘制半透明底框 (使用基础坐标)
        hud_bg = pygame.Surface((panel_width, panel_height))
        hud_bg.set_alpha(180)
        hud_bg.fill(self.TEAL)
        surface.blit(hud_bg, (base_x, base_y))
        
        # 2. 准备字体
        font_small = pygame.font.SysFont("Arial", 16)
        font_bold = pygame.font.SysFont("Arial", 16, bold=True)
        
        # 3. 状态颜色逻辑
        if self.gps_status == "3D Fix":
            status_color = self.GREEN# 绿色
        elif self.gps_status == "WPS Fix":
            status_color = self.BLUE # 蓝色
        else:
            status_color = self.YELLOW # 黄色
            
        # 4. 渲染文字
        txt_status = font_bold.render(f"SYS: {self.gps_status}", True, status_color)
        txt_sats = font_small.render(f"SATS: {self.sats} Locked", True, (200, 200, 200))
        txt_alt = font_small.render(f"ALT: {self.alt} m", True, (200, 200, 200))
        
        # 5. 核心：文字的坐标相对于 base_x 和 base_y 进行偏移
        surface.blit(txt_status, (base_x + 10, base_y + 5))
        surface.blit(txt_sats,   (base_x + 10, base_y + 30))
        surface.blit(txt_alt,    (base_x + 10, base_y + 50))

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

    def _refresh_map_view(self):
        """当缩放或平移发生时，重新计算路线像素并重绘背景"""
        if self.projector:
            # 更新投影器的视图状态
            self.projector.set_view(self.zoom_level, self.pan_x, self.pan_y)
            
            # 重新提取当前 GPX 路书的原始经纬度数据并进行像素转换
            # (由于我们之前只存了像素，为了支持无损缩放，我们要把原始经纬度存下来)
            if hasattr(self, 'current_route_points'):
                self.route_pixels = [self.projector.to_pixel(p['lat'], p['lon']) for p in self.current_route_points]
            
            # 重新绘制静态背景
            self._draw_static_background()

    def on_confirm(self, index):
        """处理地图界面的菜单确认动作"""
        if self.current_menu_level == 'main':
            if index == 0:
                self.change_menu_level('route_menu') # 跳入选择路线子菜单
            elif index == 1:
                self.map_style = 'light' if self.map_style == 'dark' else 'dark'
                self._draw_static_background()
            elif index == 2:
                print("缩放功能")
                self.change_menu_level('zoom') # 跳入地图缩放菜单
            elif index == 3:
                print("change compass statues")
                self.compass_status=not self.compass_status
                self.menus['main'][len(self.menus['main'])-1] = f"5. Compass: {"ON" if self.compass_status else "OFF"}"
            elif index == 4: # 5. Compass calibrate
                if hasattr(self, 'calibrate_callback') and self.calibrate_callback:
                    print("\n⚠️ 即将冻结屏幕进行校准，请看终端提示！")
                    # 可以在这加个变量，在屏幕上画个“校准中”的提示
                    
                    # 真正执行硬件校准 (这会让屏幕暂停刷新 30 秒)
                    self.calibrate_callback(duration=30) 
                    
                    print("✅ 校准完毕，系统恢复运行！")
                else:
                    print("❌ 未检测到真实的指南针硬件，无法校准！")

        elif self.current_menu_level == 'zoom':
            if index == 0: self.change_menu_level('select_area') # 跳入平移菜单
            elif index == 1: 
                self.zoom_level *= 1.3  # 放大 1.3 倍
                self._refresh_map_view()
            elif index == 2: 
                self.zoom_level /= 1.3  # 缩小
                self._refresh_map_view()
            # ==========================================
            # ⭐️ 触发手动 Wi-Fi 定位
            # ==========================================
            elif index == 3: # 4. WiFi location
                if hasattr(self, 'wifi_locate_callback') and self.wifi_locate_callback:
                    print("\n📡 正在手动触发 Wi-Fi/IP 定位，请稍候...")
                    # 可以在屏幕上画个提示，或者直接执行（会卡顿几秒钟）
                    self.wifi_locate_callback()
                else:
                    print("❌ Wi-Fi 定位模块未接入！")
            elif index == 4: self.change_menu_level('main')

        elif self.current_menu_level == 'select_area':
            # 注意：如果想让地图往下走，代表视野往上走，所以 offset 是正数
            if index == 0:   # Up (视野向上，地图向下)
                self.pan_y += self.pan_step
                self._refresh_map_view()
            elif index == 1: # Down
                self.pan_y -= self.pan_step
                self._refresh_map_view()
            elif index == 2: # Left
                self.pan_x += self.pan_step
                self._refresh_map_view()
            elif index == 3: # Right
                self.pan_x -= self.pan_step
                self._refresh_map_view()
            elif index == 4: # Back to my location (极致数学之美)
                if self.lat is not None and self.lon is not None and self.projector:
                    # 获取当前所在地的未缩放基准坐标
                    raw_x = self.projector.margin + ((self.lon - self.projector.min_lon) * self.projector.lon_scale_factor) * self.projector.base_scale
                    raw_y = self.projector.margin + (self.projector.max_lat - self.lat) * self.projector.base_scale
                    
                    # 逆向推算偏移量，确保当前位置的最终 X, Y 等于屏幕中心点
                    self.pan_x = -(raw_x - self.projector.center_x) * self.zoom_level
                    self.pan_y = -(raw_y - self.projector.center_y) * self.zoom_level
                    self._refresh_map_view()
                    print("已重新居中到当前 GPS 定位！")
                else:
                    print("⚠️ 尚未获取到有效的 GPS 坐标，无法居中。")
            elif index == 5:
                self.pan_x = 0
                self.pan_y = 0
                self.zoom_level = 1
                self._refresh_map_view()
            elif index == 6: 
                self.change_menu_level('zoom')

        elif self.current_menu_level == 'route_menu':
            # 判断是不是按了返回键
            if index == len(self.gpx_paths) or not self.gpx_paths:
                self.change_menu_level('main')
            else:
                # 加载选中的路书
                selected_gpx = self.gpx_paths[index]
                self._load_gpx_and_project(selected_gpx)
                # 加载完成后，自动退回主菜单，保持界面清爽
                self.change_menu_level('main')

    def _load_gpx_and_project(self, filepath):
        """核心业务逻辑：读取 GPX -> 提取坐标 -> 重新实例化投影器 -> 重绘画布"""
        try:
            print(f"正在解析路线: {filepath} ...")
            points = []
            with open(filepath, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
                for track in gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            points.append({'lat': point.latitude, 'lon': point.longitude})
            
            if len(points) < 2:
                print("⚠️ GPX 文件中没有足够的轨迹点！")
                return

            # ==================================================
            # ⭐️ 把原始的、绝对精确的经纬度列表存入对象的属性中，永久保存！
            # 格式类似于：[{'lat': 30.25, 'lon': 120.15}, {'lat': 30.26, 'lon': 120.16} ...]
            self.current_route_points = points  
            # ==================================================

            # 重置视图状态（每次加载新路书，默认居中且不缩放）
            self.zoom_level = 1.0
            self.pan_x = 0
            self.pan_y = 0

            # 重新实例化投影器 (自动适应新路线的比例尺)
            self.projector = MapProjector(points, self.width, self.height)
            self.route_pixels = [self.projector.to_pixel(p['lat'], p['lon']) for p in points]
            
            # 路线变了，必须重新画底图
            self._draw_static_background()
            print("✅ 路线加载并投影成功！")
            
        except Exception as e:
            print(f"❌ 解析 GPX 失败: {e}")

    def _calculate_navigation(self):
        """核心导航算法：计算偏航距离和指向目标的角度"""
        # 如果没有路线、没有定位、或者没有指南针，就无法导航
        if not hasattr(self, 'current_route_points') or not self.current_route_points:
            return None, None
        if self.lat is None or self.lon is None or self.heading is None:
            return None, None

        min_dist = float('inf')
        closest_index = 0
        
        # 1. 遍历轨迹，找到离我当前位置最近的那个点
        # (注：如果路线很长，这里可以优化为只搜索上次位置附近，目前先暴力全搜)
        for i, point in enumerate(self.current_route_points):
            dist = calc_distance(self.lat, self.lon, point['lat'], point['lon'])
            if dist < min_dist:
                min_dist = dist
                closest_index = i

        # 2. 设定“目标点” (Lookahead Point)
        # 我们不能直接指着最近的点，否则一旦踩在线上箭头就会乱转。
        # 我们要指向前方大概 5 个点的位置 (相当于看向远处的路标)
        lookahead_offset = 5
        target_index = min(closest_index + lookahead_offset, len(self.current_route_points) - 1)
        target_point = self.current_route_points[target_index]

        # 3. 计算“目标绝对方位角”
        target_bearing = calc_bearing(
            self.lat, self.lon, 
            target_point['lat'], target_point['lon']
        )

        # 4. 计算“相对指针角度” (屏幕上的箭头该怎么转)
        # 相对角度 = 目标方位角 - 我当前的身体朝向
        relative_angle = target_bearing - self.heading
        
        # 将角度规范化到 -180 到 180 度之间
        relative_angle = (relative_angle + 180) % 360 - 180

        # 返回：偏离轨道的距离(米), 箭头需要旋转的角度
        return min_dist, relative_angle

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
        
        # 壁纸
        default_wallpaper = './wallpaper/Cherry.png'
        self.current_wallpaper_path = cfg.get('wallpaper_path', default_wallpaper)
        if 'desktop' in self.screens:
                self.screens['desktop'].selected_path = self.current_wallpaper_path
        if 'map' in self.screens:
            self.screens['map'].wifi_locate_callback = self.manual_wifi_locate
        # 增加一些变量来记住 WPS 坐标
        self.wps_lat = None
        self.wps_lon = None
        self.wps_status_text = ""
    
    def run(self):
        running = True
        # 实例化你自己的硬件类！
        # --- ⭐️ 挂载物理摇杆驱动 ---
        try:
            self.joystick = DigitalJoystick()
        except Exception as e:
            print(f"⚠️ 摇杆驱动加载失败 (可能是没接线或在没有 GPIO 的电脑上运行): {e}")
        # GPS
        print("正在初始化 ATGM336H GPS 硬件...")
        try:
            self.gps = GPSModule(port='/dev/ttyS0', baudrate=9600)
            self.has_gps = True
        except Exception as e:
            print(f"GPS 加载失败: {e}")
            self.has_gps = False
        self.lat, self.lon = 30.259885, 120.157252
        self.lat=30.855322 
        self.lon=120.154895
        self.alt, self.sats = 0, 0
        self.gps_status = "search star"
        # compass
        print("正在初始化 LSM303D 指南针硬件...")
        try:
            self.compass = Compass(i2c_address=0x1E, filter_size=5)
            self.has_compass = True
            # ==========================================
            # ⭐️ 桥接：把校准函数的遥控器递给地图界面！
            # 假设你的地图界面在 self.screens 里的名字叫 'map'
            # ==========================================
            if 'map' in self.screens:
                self.screens['map'].calibrate_callback = self.compass.calibrate
        except Exception as e:
            print(f"指南针加载失败，将使用模拟数据。原因: {e}")
            self.has_compass = False
            self.sim_heading = 0
        # wifi
        self.wps = WifiLocator()

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
            # 读取 GPS
            if self.has_gps:
                gps_data = self.gps.get_location()
                if gps_data:
                    # 判断是“搜星中”还是“已定位”
                    if "status" in gps_data and gps_data["sats"] >= 4:
                        self.gps_status = gps_data["status"]
                        self.lat = gps_data["lat"]  # 纬度
                        self.lon = gps_data["lon"]  # 经度
                        self.alt = gps_data["alt"]  # 海拔
                        self.sats = gps_data["sats"]# 可用卫星
            # 优先级 1：真实的物理 GPS (如果有信号)
            if self.has_gps and gps_data and gps_data.get("sats", 0) >= 4:
                self.lat = gps_data["lat"]
                self.lon = gps_data["lon"]
                self.gps_status = "3D Fix"  
            # 优先级 2：如果 GPS 没信号，但用户刚才手动触发了 WPS 并且成功了
            elif self.wps_lat is not None and self.wps_lon is not None:
                self.lat = self.wps_lat
                self.lon = self.wps_lon
                self.gps_status = self.wps_status_text
            # ==========================================
            # ⭐️ 读取指南针
            # ==========================================
            # 读取指南针
            if self.has_compass:
                # 直接调用你代码里的 get_heading() 方法
                self.heading = self.compass.get_heading()
            else:
                # 硬件没接好时的备用假数据
                sim_heading = (sim_heading + 1) % 360
                self.heading = sim_heading
            current_sensor_data = {
                'heading': self.heading,
                'lat': self.lat, 
                'lon': self.lon, 
                'alt': self.alt,
                'sats': self.sats,
                'gps_status': self.gps_status
            }
            current_screen.feed_data(**current_sensor_data)
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

    def manual_wifi_locate(self):
        """用户在菜单中手动点击 WiFi Location 时触发此函数"""
        loc_data = self.wps.get_location()
        
        if loc_data:
            # 获取成功！把数据存起来
            self.wps_lat = loc_data['lat']
            self.wps_lon = loc_data['lon']
            self.wps_status_text = f"WPS Fix ({int(loc_data['accuracy'])}m)"

            print("\n=======================================================")
            print(f"📍 IP 辅助定位成功！")
            print(f"🌐 纬度: {loc_data['lat']}, 经度: {loc_data['lon']}")
            print(f"🏠 大致区域: {loc_data['address']}")
            print(f"🎯 误差精度: 约 {loc_data['accuracy']} 米 (城市级定位)")
            print("=======================================================\n")
            
        else:
            self.wps_status_text = "WPS Failed"
            print("❌ 定位失败。")

if __name__ == "__main__":
    app = ScreenManager()
    app.run()