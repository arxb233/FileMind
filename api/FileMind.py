import os
import sys
import json
import datetime
import subprocess
import webbrowser
import logging
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

def filter_development_warning(record):
    msg = record.getMessage()
    return not (msg.startswith("WARNING: This is a development server") or 
                "Do not use it in a production deployment" in msg)

logging.getLogger("werkzeug").addFilter(filter_development_warning)

# ------------------- 工具函数 -------------------
def get_resource_path(rel_path):
    try:
        base = sys._MEIPASS  # PyInstaller 打包后临时路径
    except Exception:
        base = os.path.abspath(".")
    return os.path.join(base, rel_path)

# ------------------- Markmap 树生成 -------------------
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
    path = request.args.get("path", ROOT_FOLDER)
    md = build_markmap_tree(path)
    return jsonify({"markdown": md})

@app.route("/api/info", methods=["GET"])
def api_info():
    path = request.args.get("path", ROOT_FOLDER)
    total_files = sum(len(files) for _, _, files in os.walk(path))
    total_folders = sum(len(dirs) for _, dirs, _ in os.walk(path))
    info = {
        "path": path,
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

# ------------------- 盘符与目录 API -------------------
@app.route("/api/drives", methods=["GET"])
def api_drives():
    drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    return jsonify(drives)

@app.route("/api/list", methods=["GET"])
def api_list():
    path = request.args.get("path")
    if not path or not os.path.exists(path):
        return jsonify({"folders": [], "files": []})
    folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f)) and not f.startswith(".")]
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and not f.startswith(".")]
    return jsonify({"folders": folders, "files": files})

# ------------------- 提供前端 -------------------
def res(path):
    base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__) + "/.."
    return os.path.join(base, path)
@app.route("/")
@app.route("/<path:p>")
def static_files(p="index.html"):
    file_path = res(f"web/{p}")
    if os.path.isfile(file_path):
        return send_file(file_path)
    else:
        # 任何不存在的静态文件都返回 index.html（支持前端路由）
        return send_file(res("web/index.html"))

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
