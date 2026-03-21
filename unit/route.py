import gpxpy
import gpxpy.gpx
import folium
import pygame
import os
import math

def load_gpx_route(file_path):
    """
    加载并解析 GPX 文件，提取所有轨迹点
    """
    print(f"正在读取路线文件: {file_path} ...")
    route_points = []
    
    try:
        # 打开并解析文件
        with open(file_path, 'r', encoding='utf-8') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            
        # 遍历：轨迹 -> 轨迹段 -> 具体的点
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    # 将提取到的坐标打包成字典存入列表
                    route_points.append({
                        'lat': point.latitude,
                        'lon': point.longitude,
                        'ele': point.elevation # 海拔可能为 None，取决于记录设备
                    })
                    
        print(f"✅ 解析成功！共提取到 {len(route_points)} 个轨迹点。")
        return route_points

    except FileNotFoundError:
        print(f"❌ 错误：找不到文件，请确认 {file_path} 路径是否正确。")
        return None
    except Exception as e:
        print(f"❌ 解析 GPX 文件时发生错误: {e}")
        return None

def generate_html_map(route_points,out_html):
    """根据坐标点列表生成交互式 HTML 地图"""
    if not route_points or len(route_points) < 2:
        print("❌ 坐标点不足，无法绘制地图线。")
        return
    
    print("正在生成地图...")

    # --- 核心修改点：将字典列表转换为 Folium 需要的 [lat, lon] 列表 ---
    coords = [[p['lat'], p['lon']] for p in route_points]

    # 计算路线的中心点，用于地图的初始中心
    center_lat = sum(p[0] for p in coords) / len(coords)
    center_lon = sum(p[1] for p in coords) / len(coords)

    # 创建基础地图对象
    my_map = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=14,  # 初始缩放比例
        control_scale=True # 显示比例尺
    )

    # 使用转换后的 coords 绘制路线
    folium.PolyLine(
        coords,
        color="#3388ff", # 线条颜色（蓝色）
        weight=5,        # 线条粗细
        opacity=0.8,     # 透明度
        tooltip="Map"    # 鼠标悬停提示
    ).add_to(my_map)

    # 标记起点 (使用 coords 的第一个点)
    folium.Marker(
        location=coords[0],
        popup="起点",
        icon=folium.Icon(color='green', icon='play')
    ).add_to(my_map)

    # 标记终点 (使用 coords 的最后一个点)
    folium.Marker(
        location=coords[-1],
        popup="终点",
        icon=folium.Icon(color='red', icon='stop')
    ).add_to(my_map)

    # 自动调整地图视野，包裹整条路线
    my_map.fit_bounds([coords[0], coords[-1]])

    # 保存为 HTML 文件
    my_map.save(out_html)
    print(f"✅ 地图已成功保存到: {out_html}")

def display_html(title="路线",url="/home/ma/AssistDoc/map/westlake_map.html",width=800,height=800,resizable=True):
    import webview
    window = webview.create_window(
        title=title, 
        url=url,
        width=width, 
        height=height,
        resizable=resizable
    )
    
    webview.start()

# --- 坐标转换器类 ---
class MapProjector:
    def __init__(self, points, screen_width, screen_height, margin=50):
        self.width = screen_width
        self.height = screen_height
        self.margin = margin
        
        # 1. 找出路线的最东、西、南、北边界
        self.min_lat = min(p['lat'] for p in points)
        self.max_lat = max(p['lat'] for p in points)
        self.min_lon = min(p['lon'] for p in points)
        self.max_lon = max(p['lon'] for p in points)
        
        # 2. 计算地球曲率补偿（可选，但加上会更精准，防止地图变形）
        # 在杭州西湖纬度（约30度），经度的物理距离比纬度短
        mid_lat = math.radians((self.min_lat + self.max_lat) / 2)
        self.lon_scale_factor = math.cos(mid_lat)
        
        # 3. 计算缩放比例 (Scale)
        lon_diff = (self.max_lon - self.min_lon) * self.lon_scale_factor
        lat_diff = self.max_lat - self.min_lat
        
        draw_w = self.width - 2 * margin
        draw_h = self.height - 2 * margin
        
        # 取长宽中较小的缩放比，保证路线能完整显示且不变形
        if lon_diff == 0 or lat_diff == 0:
            self.scale = 1 # 防止单点除零报错
        else:
            self.scale = min(draw_w / lon_diff, draw_h / lat_diff)

    def to_pixel(self, lat, lon):
        """将真实的经纬度转换为屏幕上的 X, Y 像素坐标"""
        # X 轴映射 (经度)
        x = self.margin + ((lon - self.min_lon) * self.lon_scale_factor) * self.scale
        # Y 轴映射 (纬度，注意 Pygame 的 Y 轴是朝下的，所以要用 max_lat 减去当前 lat)
        y = self.margin + (self.max_lat - lat) * self.scale
        
        return int(x), int(y)

class MapGUI:
    def __init__(self, route_points, width=800, height=600, title="硬核徒步导航仪"):
        """初始化地图界面"""
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        
        # 颜色库
        self.BLACK = (20, 20, 20)
        self.DARK_GREEN = (0, 80, 0)
        self.ROUTE_COLOR = (50, 150, 255)
        self.START_COLOR = (0, 255, 0)
        self.END_COLOR = (255, 50, 50)
        self.MY_COLOR = (255, 200, 0) # 你的位置箭头颜色 (醒目的金黄色)

        # 初始化投影器并缓存路线像素点
        self.projector = MapProjector(route_points, width, height)
        self.route_pixels = [self.projector.to_pixel(p['lat'], p['lon']) for p in route_points]
        
        # 预先绘制一个静态背景 Surface (提升性能)
        self.bg_surface = pygame.Surface((self.width, self.height))
        self._draw_static_background()

    def _draw_static_background(self):
        """内部方法：绘制不会改变的背景和路线"""
        self.bg_surface.fill(self.BLACK)
        # 画网格
        for i in range(0, self.width, 50):
            pygame.draw.line(self.bg_surface, self.DARK_GREEN, (i, 0), (i, self.height), 1)
        for i in range(0, self.height, 50):
            pygame.draw.line(self.bg_surface, self.DARK_GREEN, (0, i), (self.width, i), 1)
        # 画路线
        pygame.draw.lines(self.bg_surface, self.ROUTE_COLOR, False, self.route_pixels, 4)
        # 画起点终点
        pygame.draw.circle(self.bg_surface, self.START_COLOR, self.route_pixels[0], 6)
        pygame.draw.circle(self.bg_surface, self.END_COLOR, self.route_pixels[-1], 6)

    def draw_frame(self, current_lat=None, current_lon=None, heading=0):
        """
        绘制每一帧画面
        :param current_lat: 当前纬度 (如果为 None 则不画箭头)
        :param current_lon: 当前经度
        :param heading: 当前偏角 (0-360)
        """
        # 1. 贴上静态背景和路线
        self.screen.blit(self.bg_surface, (0, 0))
        
        # 2. 如果有当前的 GPS 坐标，画出代表你自己的导航箭头
        if current_lat is not None and current_lon is not None:
            # 将你的经纬度转换为屏幕上的像素坐标
            px, py = self.projector.to_pixel(current_lat, current_lon)
            self._draw_navigation_arrow(self.screen, self.MY_COLOR, (px, py), 15, heading)
            
        # 3. 刷新屏幕
        pygame.display.flip()

    def _draw_navigation_arrow(self, surface, color, center, radius, heading):
        """内部方法：画一个带有指向性的箭头 (类似战斗机标志)"""
        # 将指南针角度 (北=0) 转换为 Pygame 角度体系
        angle_rad = math.radians(heading - 90)
        
        # 计算箭头的三个顶点
        tip = (center[0] + radius * math.cos(angle_rad), 
               center[1] + radius * math.sin(angle_rad))
        left_wing = (center[0] + radius * 0.8 * math.cos(angle_rad + 2.5), 
                     center[1] + radius * 0.8 * math.sin(angle_rad + 2.5))
        right_wing = (center[0] + radius * 0.8 * math.cos(angle_rad - 2.5), 
                      center[1] + radius * 0.8 * math.sin(angle_rad - 2.5))
        
        pygame.draw.polygon(surface, color, [tip, left_wing, right_wing])

    def check_quit(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
        return False

    def close(self):
        pygame.quit()

# --- 测试运行 ---
if __name__ == "__main__":
    # 使用绝对路径
    westlake_gpx_path = '/home/ma/AssistDoc/map/westlake.gpx'
    out_html = "/home/ma/AssistDoc/map/westlake_map.html"
    points = load_gpx_route(westlake_gpx_path)
    
    # 如果成功提取到了点，打印出前三个和最后一个点看看
    if points and len(points) > 0:
        print("-" * 30)
        print("路线预览：")
        print(f"  起点坐标: 纬度 {points[0]['lat']:.6f}, 经度 {points[0]['lon']:.6f}")
        
        if len(points) > 3:
            print(f"  途经点 2: 纬度 {points[1]['lat']:.6f}, 经度 {points[1]['lon']:.6f}")
            print(f"  途经点 3: 纬度 {points[2]['lat']:.6f}, 经度 {points[2]['lon']:.6f}")
            print("  ...")
            
        print(f"  终点坐标: 纬度 {points[-1]['lat']:.6f}, 经度 {points[-1]['lon']:.6f}")
        print("-" * 30)
    # generate_html_map(points, out_html)

    # # 显示路径
    # display_html(out_html)

    gui = MapGUI(points, width=800, height=600, title="西湖导航仪 v1.0")
    running = True
    while running:
        gui.draw_frame(current_lat=None, current_lon=None, heading=20)
        gui.clock.tick(20)

    gui.close()
    print("程序已安全退出。")