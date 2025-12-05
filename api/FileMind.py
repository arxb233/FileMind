import os
import http.server
import socketserver
import webbrowser
import subprocess
from tkinter import Tk, filedialog
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
            item_clean = item.replace("\t", "    ").strip()
            abs_path = os.path.abspath(item_path).replace("\\", "/")
            if os.path.isdir(item_path):
                lines.append(f"{indent}- <a href='#' data-path='{abs_path}' data-type='folder' title='{abs_path}'>{item_clean}/</a>")
                walk(item_path, level + 1)
            else:
                lines.append(f"{indent}- <a href='#' data-path='{abs_path}' data-type='file' title='{abs_path}'>{item_clean}</a>")

    walk(root_path, 1)
    return "\n".join(lines)

# ================== 2. 生成 HTML ==================
import datetime
import os
import datetime

def generate_html(markdown, root_folder):
    folder_name = os.path.basename(root_folder) or root_folder
    total_files = sum([len(files) for _, _, files in os.walk(root_folder)])
    total_folders = sum([len(dirs) for _, dirs, _ in os.walk(root_folder)])
    generated_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>FileMind – 文件思维导图 - Baris</title>
<style>
  /* 页面布局 */
  html, body {{
      height: 100%;
      margin: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      background:#f0f2f5;
  }}

  /* 顶部 header */
  header {{
      background: #276FF5;
      color: white;
      padding: 16px 24px;
      margin-bottom: 12px; 
      box-shadow: 0 2px 6px rgba(0,0,0,0.2);
      flex: 0 0 auto;
  }}
  header h1 {{ margin:0; font-size: 24px; }}
  header p {{ margin:4px 0 0 0; font-size: 14px; color: #d0e0ff; }}

  /* Markmap 容器 */
  .markmap {{
      flex: 1; /* 占满剩余空间 */
      background: #f0f8ff; /* 浅蓝色背景 */
      border-radius: 6px;
      box-shadow: 0 1px 6px rgba(0,0,0,0.1);
      display: flex; /* 保证 svg 占满容器 */
  }}
  svg.markmap {{
      width: 100%;
      height: 100%;
  }}

  /* 文件/文件夹节点样式 */
  a {{
      text-decoration: none;
      cursor: pointer;
      padding: 2px 4px;
      border-radius: 3px;
  }}
  a[data-type="folder"] {{ color: #1a73e8; font-weight: bold; }}
  a[data-type="file"] {{ color: #555;font-weight: bold;  }}
  a:hover {{ background: rgba(26,115,232,0.1); }}

  /* 可选：调整 Markmap 节点字体大小 */
  svg.markmap text {{
      font-size: 16px;
  }}
</style>
<script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.18"></script>
<script>
function openPath(path, type) {{
    fetch('/open_path', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{ path: path, type: type }})
    }});
}}
document.addEventListener('click', function(e){{
    if(e.target.tagName==='A' && e.target.dataset.path){{
        e.preventDefault();
        openPath(e.target.dataset.path, e.target.dataset.type);
    }}
}});
</script>
</head>
<body>
<header>
  <h1>FileMind – 文件思维导图 - Baris</h1>
  <p>路径: {root_folder} | 文件夹: {total_folders} | 文件: {total_files} | 生成时间: {generated_time}</p>
</header>
<div class="markmap">
  <script type="text/template">
{markdown}
  </script>
</div>
</body>
</html>"""
    return html


# ================== 3. HTTP 服务 ==================
class Handler(http.server.SimpleHTTPRequestHandler):
    html_content = ""

    def do_GET(self):
        if self.path == "/" or self.path.endswith(".html"):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self.html_content.encode("utf-8"))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/open_path":
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                data = json.loads(body)
                path = data.get("path")
                type_ = data.get("type")
                if path and os.path.exists(path):
                    path = os.path.abspath(path)
                    if os.name == 'nt':
                        if type_ == 'folder':
                            subprocess.Popen(['explorer', path])
                        else:
                            os.startfile(path)
                    else:
                        subprocess.Popen(['open', path])
            except Exception as e:
                print("打开失败:", e)
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def start_server(html, port=8101):
    Handler.html_content = html
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print(f"✓ 本地 HTTP 服务启动：http://localhost:{port}")
        webbrowser.open(f"http://localhost:{port}")
        httpd.serve_forever()

# ================== 4. 主程序 ==================
if __name__ == "__main__":
    print("=== FileMind – 文件思维导图 - Baris ===")
    Tk().withdraw()
    folder = filedialog.askdirectory(title="请选择要生成思维导图的文件夹")
    if not folder:
        print("未选择文件夹，已退出")
        exit()

    md = build_markmap_tree(folder)
    html = generate_html(md, folder)  # ⚠ 这里要传 folder
    start_server(html, port=8101)

