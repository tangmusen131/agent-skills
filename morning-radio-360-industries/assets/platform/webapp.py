# -*- coding: utf-8 -*-
"""
行业早安电台 · 网页版（webapp.py）
=================================
电脑浏览器操作：选行业 → 传素材 → 出文案（可改）→ 一键生成视频 → 下载

启动：
  python webapp.py                 # 默认仅本机 http://127.0.0.1:8000
  python webapp.py 127.0.0.1 8000  # 同上，显式指定端口

依赖：Flask（渲染环境已装）；渲染底层复用 daily_pipeline.py + render.py
多商家工作区：每个商家一个 ws_id，素材互不干扰。
默认只监听本机回环地址。若改为其它监听地址供局域网使用，须自行加登录校验、
HTTPS 与反向代理——本模板不附带鉴权。
"""
import os
import sys
import json
import uuid
import glob
import threading
import datetime

from flask import Flask, request, jsonify, send_from_directory, render_template_string

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import daily_pipeline
from industries import INDUSTRIES, load_copy_module

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024  # 单次上传上限 512MB

ALLOWED_UPLOAD_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

WORKSPACES_ROOT = os.path.join(SCRIPT_DIR, "workspaces")   # 每商家素材
OUTPUT_ROOT = os.path.join(SCRIPT_DIR, "output")           # 产物总目录
os.makedirs(WORKSPACES_ROOT, exist_ok=True)

# 渲染任务表（内存）：task_id -> {status, step, desc, result, error, thread}
TASKS = {}
RENDER_LOCK = threading.Lock()  # 一次渲一条，避免 CPU 打满
RENDER_SEMAPHORE = threading.Semaphore(1)


# ============= 工作区 =============
def _ws_dir(ws_id):
    return os.path.join(WORKSPACES_ROOT, ws_id)


def _ws_meta_path(ws_id):
    return os.path.join(_ws_dir(ws_id), "meta.json")


def _safe_ws(ws_id):
    if not ws_id or ".." in ws_id or "/" in ws_id or "\\" in ws_id:
        return None
    d = _ws_dir(ws_id)
    if not os.path.isdir(d):
        return None
    return d


# ============= 页面 =============
@app.route("/")
def index():
    html_path = os.path.join(SCRIPT_DIR, "webapp_static", "index.html")
    with open(html_path, encoding="utf-8") as f:
        return f.read()


# ============= API：工作区 =============
@app.route("/api/workspace", methods=["POST"])
def create_workspace():
    name = (request.json or {}).get("name", "").strip()[:30]
    if not name:
        return jsonify({"error": "请填写商家名称"}), 400
    ws_id = uuid.uuid4().hex[:8]
    d = _ws_dir(ws_id)
    os.makedirs(d, exist_ok=True)
    meta = {"ws_id": ws_id, "name": name, "created": datetime.datetime.now().isoformat()}
    with open(_ws_meta_path(ws_id), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    return jsonify(meta)


@app.route("/api/workspace/<ws_id>", methods=["GET"])
def get_workspace(ws_id):
    d = _safe_ws(ws_id)
    if not d:
        return jsonify({"error": "工作区不存在，请重新创建"}), 404
    with open(_ws_meta_path(ws_id), encoding="utf-8") as f:
        meta = json.load(f)
    # 汇总各行业素材上传状态
    industries_status = {}
    for iid in INDUSTRIES:
        mdir = os.path.join(d, iid)
        slots = []
        for i in range(1, 7):
            pats = [os.path.join(mdir, f"{i:02d}_*{ext}")
                    for ext in (".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v")]
            found = sorted(p for pat in pats for p in glob.glob(pat))
            slots.append(bool(found))
        industries_status[iid] = {"ready": all(slots), "slots": slots}
    meta["industries"] = industries_status
    return jsonify(meta)


# ============= API：素材上传 =============
@app.route("/api/workspace/<ws_id>/<industry>/upload", methods=["POST"])
def upload_material(ws_id, industry):
    d = _safe_ws(ws_id)
    if not d:
        return jsonify({"error": "工作区不存在"}), 404
    if industry not in INDUSTRIES:
        return jsonify({"error": "未知行业"}), 400
    slot = int(request.form.get("slot", "0"))
    if slot < 1 or slot > 6:
        return jsonify({"error": "槽位编号 1~6"}), 400
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "未收到文件"}), 400
    mdir = os.path.join(d, industry)
    os.makedirs(mdir, exist_ok=True)
    # 清掉该槽位旧文件，保留 01_ 前缀命名规则
    for old in glob.glob(os.path.join(mdir, f"{slot:02d}_*")):
        os.remove(old)
    # 只接受视频扩展名；落盘名固定为槽位前缀，忽略客户端原始文件名（防路径注入）
    raw_name = os.path.basename(f.filename or "")
    ext = os.path.splitext(raw_name)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTS:
        return jsonify({
            "error": f"仅支持视频格式: {', '.join(sorted(ALLOWED_UPLOAD_EXTS))}"
        }), 400
    save_path = os.path.join(mdir, f"{slot:02d}_素材{ext}")
    f.save(save_path)
    return jsonify({"ok": True, "slot": slot, "file": os.path.basename(save_path)})


# ============= API：文案 =============
@app.route("/api/copy", methods=["POST"])
def gen_copy():
    data = request.json or {}
    industry = data.get("industry")
    if industry not in INDUSTRIES:
        return jsonify({"error": "未知行业"}), 400
    date_str = data.get("date") or datetime.date.today().isoformat()
    try:
        date = datetime.date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "日期格式应为 YYYY-MM-DD"}), 400
    copy_mod = load_copy_module(industry)
    copy = copy_mod.build(date)
    return jsonify(copy)


# ============= API：渲染 =============
def _render_worker(task_id, ws_id, industry, date, narration):
    t = TASKS[task_id]
    with RENDER_SEMAPHORE:
        try:
            d = _ws_dir(ws_id)
            materials_dir = os.path.join(d, industry)
            out_dir = os.path.join(OUTPUT_ROOT, ws_id, f"{industry}_{date.isoformat()}")

            def cb(step, desc):
                t["step"], t["desc"] = step, desc

            result = daily_pipeline.run(
                industry, date,
                narration_override=narration,
                materials_dir=materials_dir,
                out_dir=out_dir,
                progress_cb=cb,
            )
            t["status"] = "done"
            t["result"] = {
                "cover": os.path.relpath(result["cover"], SCRIPT_DIR).replace("\\", "/"),
                "final": os.path.relpath(result["final"], SCRIPT_DIR).replace("\\", "/"),
            }
        except Exception as e:
            t["status"] = "error"
            t["error"] = str(e)


@app.route("/api/render", methods=["POST"])
def start_render():
    data = request.json or {}
    ws_id = data.get("ws_id", "")
    industry = data.get("industry")
    d = _safe_ws(ws_id)
    if not d:
        return jsonify({"error": "工作区不存在，请重新创建"}), 404
    if industry not in INDUSTRIES:
        return jsonify({"error": "未知行业"}), 400
    # 校验素材齐全
    mdir = os.path.join(d, industry)
    for i in range(1, 7):
        pats = [os.path.join(mdir, f"{i:02d}_*{ext}")
                for ext in (".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v")]
        if not any(glob.glob(p) for p in pats):
            return jsonify({"error": f"素材槽位 {i:02d} 还没上传，请先传齐 6 段素材"}), 400
    date_str = data.get("date") or datetime.date.today().isoformat()
    date = datetime.date.fromisoformat(date_str)
    narration = (data.get("narration") or "").strip() or None

    task_id = uuid.uuid4().hex[:8]
    TASKS[task_id] = {"status": "running", "step": 0, "desc": "排队中", "error": None}
    th = threading.Thread(target=_render_worker,
                          args=(task_id, ws_id, industry, date, narration), daemon=True)
    TASKS[task_id]["thread"] = th
    th.start()
    return jsonify({"task_id": task_id})


@app.route("/api/task/<task_id>")
def task_status(task_id):
    t = TASKS.get(task_id)
    if not t:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify({k: v for k, v in t.items() if k != "thread"})


# ============= 产物下载 =============
def _under_root(path, root):
    """确认 path 落在 root 之内（含 root 自身），避免前缀误判与目录穿越。"""
    root_abs = os.path.abspath(root)
    path_abs = os.path.abspath(path)
    try:
        common = os.path.commonpath([root_abs, path_abs])
    except ValueError:
        return False
    return common == root_abs


@app.route("/files/<path:relpath>")
def files(relpath):
    # 仅允许下载平台目录下的产物；拒绝 .. 与越界路径
    if ".." in relpath.replace("\\", "/").split("/"):
        return jsonify({"error": "路径不允许"}), 403
    full = os.path.normpath(os.path.join(SCRIPT_DIR, relpath))
    if not _under_root(full, SCRIPT_DIR):
        return jsonify({"error": "路径不允许"}), 403
    # 进一步限制为 output/ 下的成片与封面（网页版下载入口）
    if not _under_root(full, OUTPUT_ROOT):
        return jsonify({"error": "路径不允许"}), 403
    if not os.path.isfile(full):
        return jsonify({"error": "文件不存在"}), 404
    return send_from_directory(os.path.dirname(full), os.path.basename(full))


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    print(f"行业早安电台网页版: http://{host}:{port}")
    app.run(host=host, port=port, threaded=True)
