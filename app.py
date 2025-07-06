import os
import sys
import ctypes
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import urllib.parse

PORT = 48835
HOST = '127.0.0.1'

def show_alert_box(message):
    """
    显示强制置顶的消息框
    """
    # 定义消息框标志
    MB_ICONWARNING = 0x30
    MB_SYSTEMMODAL = 0x1000
    MB_SETFOREGROUND = 0x10000
    MB_TOPMOST = 0x40000
    
    # 组合标志
    flags = MB_ICONWARNING | MB_SYSTEMMODAL | MB_SETFOREGROUND | MB_TOPMOST
    
    # 调用API显示置顶消息框
    ctypes.windll.user32.MessageBoxW(
        0,
        f"{message}\n\n"
        f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "请立即查看群消息并回复！",
        "🔥 群消息紧急提醒",
        flags
    )

class RequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        path = super().translate_path(path)
        abs_path = os.path.abspath(path)
        if not abs_path.startswith(os.getcwd()):
            return os.path.join(os.getcwd(), 'forbidden.html')
        return path
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        try:
            return super().do_GET()
        except (BrokenPipeError, ConnectionResetError):
            pass
    
    def do_POST(self):
        if self.path == '/remind':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                # 解析表单数据
                parsed_data = urllib.parse.parse_qs(post_data)
                username = parsed_data.get('username', ['匿名'])[0]
                message = parsed_data.get('message', ['群友提醒你查看群消息！'])[0]
                
                if message:
                    # 启动独立线程显示置顶弹窗
                    threading.Thread(
                        target=show_alert_box, 
                        args=(f"{username}说：{message}",),
                        daemon=True
                    ).start()
                    
                    # 响应重定向
                    self.send_response(303)
                    self.send_header('Location', '/?success=true&username=' + urllib.parse.quote(username))
                    self.end_headers()
                    return
                else:
                    self.send_error(400, "消息不能为空")
                    return
            except Exception as e:
                print(f"⚠️ 处理POST请求出错: {e}")
                self.send_error(500)
                return
        
        self.send_error(404)

def start_server():
    httpd = HTTPServer((HOST, PORT), RequestHandler)
    print(f"✅ 服务器运行中 | http://{HOST}:{PORT}")
    print(f"🛑 按Ctrl+C停止服务")
    httpd.serve_forever()

def setup_console():
    if sys.stdout.encoding != 'UTF-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if __name__ == '__main__':
    setup_console()
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    print("🌐 正在打开浏览器...")
    time.sleep(0.5)
    webbrowser.open(f'http://{HOST}:{PORT}')
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
        sys.exit(0)