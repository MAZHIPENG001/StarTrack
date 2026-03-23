import requests
import time

class WifiLocator:
    def __init__(self):
        """
        初始化纯 IP 网络辅助定位模块
        完全免费，无需任何 API Key，利用当前连接的宽带/基站 IP 粗略定位
        """
        # 使用免费良心的 ip-api 接口
        self.api_url = "http://ip-api.com/json/?lang=zh-CN"

    def get_location(self):
        """发送网络请求，换取 IP 所在的大致经纬度"""
        print("🌐 正在通过当前连接的 Wi-Fi/热点 IP 获取大致位置...")
        
        try:
            # 向免费 API 发送极其简单的 GET 请求
            response = requests.get(self.api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查接口是否成功返回数据
                if data.get('status') == 'success':
                    return {
                        "lat": float(data['lat']),
                        "lon": float(data['lon']),
                        # IP 定位极不精确，我们强制把误差范围设为 5000 米（5公里）
                        # 这样在你的 StarTrack OS 界面上会显示 "WPS Fix (5000m)"，提醒你这只是个粗略位置
                        "accuracy": 5000, 
                        "address": f"{data.get('regionName', '')} {data.get('city', '')}"
                    }
                else:
                    print(f"❌ 获取失败，云端提示: {data.get('message')}")
            else:
                print(f"☁️ 云端 HTTP 状态码异常: {response.status_code}") 
                
        except Exception as e:
            print(f"❌ 网络请求失败 (请检查树莓派是否连接了外网): {e}")
            
        return None

# 单独测试一下
if __name__ == "__main__":
    wps = WifiLocator()
    loc = wps.get_location()
    
    if loc:
        print("\n=======================================================")
        print(f"📍 IP 辅助定位成功！")
        print(f"🌐 纬度: {loc['lat']}, 经度: {loc['lon']}")
        print(f"🏠 大致区域: {loc['address']}")
        print(f"🎯 误差精度: 约 {loc['accuracy']} 米 (城市级定位)")
        print("=======================================================\n")
    else:
        print("❌ 定位失败。")