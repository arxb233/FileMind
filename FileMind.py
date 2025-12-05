import os
import http.server
import socketserver
import subprocess
from urllib.parse import urlparse, parse_qs
import json

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

        # ---------- 读取前端 index.html ----------
        if parsed.path == "/" or parsed.path == "/index.html":
            return super().do_GET()

        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/open":
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))

            path = data.get("path")
            type_ = data.get("type")

            try:
                if os.name == "nt":
                    if type_ == "folder":
                        subprocess.Popen(["explorer", path])
                    else:
                        os.startfile(path)
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
        httpd.serve_forever()


if __name__ == "__main__":
    root = input("请输入要生成思维导图的目录：").strip('"')
    if not os.path.isdir(root):
        print("输入错误")
        exit()

    start_server(root)
