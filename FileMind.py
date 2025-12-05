import os
import http.server
import socketserver
import subprocess
from urllib.parse import urlparse, parse_qs
import json
import webbrowser
import datetime
import sys, os

def get_resource_path(rel_path):
    try:
        # PyInstaller 打包后，临时路径
        base = sys._MEIPASS
    except Exception:
        # 开发环境
        base = os.path.abspath(".")
    return os.path.join(base, rel_path)

# ================== 1. 生成 Markmap 树 ==================
def build_markmap_tree(root_path):
    root_name = os.path.basename(root_path) or root_path
    lines = [f"- {root_name}"]

    def walk(path, level):
        if level > 6:
            return
        indent = "  " * level
        try:
            items = sorted(os.listdir(path))
        except PermissionError:
            lines.append(f"{indent}- [权限拒绝]")
            return

        for item in items:
            if item.startswith('.'):
                continue

            item_path = os.path.join(path, item)
            abs_path = os.path.abspath(item_path).replace("\\", "/")
            display = item.replace("\t", "    ").strip()

            if os.path.isdir(item_path):
                lines.append(
                    f"{indent}- <a href='#' data-path='{abs_path}' data-type='folder'>{display}/</a>"
                )
                walk(item_path, level + 1)
            else:
                lines.append(
                    f"{indent}- <a href='#' data-path='{abs_path}' data-type='file'>{display}</a>"
                )

    walk(root_path, 1)
    return "\n".join(lines)


# ================== 2. HTTP API ==================
class APIServer(http.server.SimpleHTTPRequestHandler):
    root_folder = ""

    def do_GET(self):
        parsed = urlparse(self.path)

        # ---------- /api/tree ----------
        if parsed.path == "/api/tree":
            md = build_markmap_tree(self.root_folder)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"markdown": md}).encode("utf-8"))
            return
        
        # ---------- /api/info ----------
        if parsed.path == "/api/info":
            total_files = sum(len(files) for _, _, files in os.walk(self.root_folder))
            total_folders = sum(len(dirs) for _, dirs, _ in os.walk(self.root_folder))
            info = {
                "path": self.root_folder,
                "folders": total_folders,
                "files": total_files,
                "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(info).encode())
            return

        # ---------- 读取 index.html ----------
        if parsed.path in ("/", "/index.html"):
            path = get_resource_path("index.html")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(path, "rb") as f:
                self.wfile.write(f.read())
            return


        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/open":
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))

            path = data.get("path")
            type_ = data.get("type", "file")

            try:
                # 转成 Windows 正确路径
                win_path = os.path.abspath(path)

                if os.name == "nt":
                    if type_ == "folder":
                        # 必须使用 explorer + 绝对路径
                        subprocess.Popen(["explorer", win_path])
                    else:
                        os.startfile(win_path)
                else:
                    subprocess.Popen(["open", path])

            except Exception as e:
                print("打开失败:", e)

            self.send_response(200)
            self.end_headers()
            return


# ================== 3. 启动服务 ==================
def start_server(root, port=8101):
    APIServer.root_folder = root
    with socketserver.TCPServer(("", port), APIServer) as httpd:
        print(f"✓ API & Web 服务启动：http://localhost:{port}")
        webbrowser.open(f"http://localhost:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    root = os.getcwd()
    print(f"当前目录：{root}")
    start_server(root)
