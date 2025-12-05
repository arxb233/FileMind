import os
import json
import datetime
import subprocess
import webbrowser
import sys
import logging
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
# ------------------- 隐藏 Flask/werkzeug 日志 -------------------
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # 只显示错误，忽略 info/warning

# ------------------- 工具函数 -------------------
def get_resource_path(rel_path):
    try:
        # PyInstaller 打包后，临时路径
        base = sys._MEIPASS
    except Exception:
        base = os.path.abspath(".")
    return os.path.join(base, rel_path)

# ------------------- 生成 Markmap 树 -------------------
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
                lines.append(f"{indent}- <a href='#' data-path='{abs_path}' data-type='folder'>{display}/</a>")
                walk(item_path, level + 1)
            else:
                lines.append(f"{indent}- <a href='#' data-path='{abs_path}' data-type='file'>{display}</a>")

    walk(root_path, 1)
    return "\n".join(lines)

# ------------------- API -------------------
ROOT_FOLDER = os.getcwd()

@app.route("/api/tree", methods=["GET"])
def api_tree():
    md = build_markmap_tree(ROOT_FOLDER)
    return jsonify({"markdown": md})

@app.route("/api/info", methods=["GET"])
def api_info():
    total_files = sum(len(files) for _, _, files in os.walk(ROOT_FOLDER))
    total_folders = sum(len(dirs) for _, dirs, _ in os.walk(ROOT_FOLDER))
    info = {
        "path": ROOT_FOLDER,
        "folders": total_folders,
        "files": total_files,
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return jsonify(info)

@app.route("/api/open", methods=["POST"])
def api_open():
    data = request.json
    path = data.get("path")
    type_ = data.get("type", "file")
    try:
        win_path = os.path.abspath(path)
        if os.name == "nt":
            if type_ == "folder":
                subprocess.Popen(["explorer", win_path])
            else:
                os.startfile(win_path)
        else:
            subprocess.Popen(["open", path])
    except Exception as e:
        print("打开失败:", e)
    return "", 200

@app.route("/", methods=["GET"])
@app.route("/index.html", methods=["GET"])
def index():
    path = get_resource_path("index.html")
    return send_file(path)

# ------------------- 启动 -------------------
def start_server(root=ROOT_FOLDER, port=8101):
    global ROOT_FOLDER
    ROOT_FOLDER = root
    url = f"http://localhost:{port}"
    print(f"✓ API & Web 服务启动：{url}")
    webbrowser.open(url)
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    print(f"当前目录：{ROOT_FOLDER}")
    start_server()
