# app.py
from flask import Flask, request, jsonify, Blueprint
import sqlite3
from datetime import datetime
from seats import seat_bp, init_seats  # ✅ 确保 seats.py 在同级目录

DATABASE = "library.db"

# ======================
# 数据库操作
# ======================
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    # 用户信息表
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE,
        password TEXT,
        name TEXT,
        register_time TEXT,
        seat_count INTEGER DEFAULT 0
    )
    """)
    # 选座流水表
    conn.execute("""
    CREATE TABLE IF NOT EXISTS seat_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        seat_number TEXT,
        action TEXT,  -- 选座/退座/暂离
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()

# ======================
# 蓝图：账户管理
# ======================
account_bp = Blueprint('account', __name__)

@account_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    student_id = data.get("student_id")
    password = data.get("password")

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (student_id, password, name, register_time) VALUES (?, ?, ?, ?)",
            (student_id, password, f"学生{student_id[-4:]}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return jsonify({"status": "success", "msg": "注册成功"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "msg": "该学号已注册"})
    finally:
        conn.close()

@account_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    student_id = data.get("student_id")
    password = data.get("password")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE student_id=? AND password=?",
        (student_id, password)
    ).fetchone()
    conn.close()

    if user:
        return jsonify({"status": "success", "user": dict(user)})
    else:
        return jsonify({"status": "error", "msg": "学号或密码错误"})

@account_bp.route("/user/<student_id>")
def get_user(student_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE student_id=?", (student_id,)).fetchone()
    conn.close()
    if not user:
        return jsonify({"status": "error", "msg": "未找到用户"})

    conn = get_db()
    logs = conn.execute(
        "SELECT * FROM seat_logs WHERE student_id=? ORDER BY id DESC LIMIT 10",
        (student_id,)
    ).fetchall()
    conn.close()

    user_dict = dict(user)
    user_dict["seat_logs"] = [dict(row) for row in logs]
    return jsonify(user_dict)

@account_bp.route("/seat_action", methods=["POST"])
def seat_action():
    data = request.json
    student_id = data.get("student_id")
    seat_number = data.get("seat_number")
    action = data.get("action")

    conn = get_db()
    conn.execute(
        "INSERT INTO seat_logs (student_id, seat_number, action, timestamp) VALUES (?, ?, ?, ?)",
        (student_id, seat_number, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    if action == "选座":
        conn.execute("UPDATE users SET seat_count = seat_count + 1 WHERE student_id=?", (student_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "msg": f"{action}记录成功"})

# ======================
# 创建 Flask 应用（供 main.py 调用）
# ======================
def create_app():
    app = Flask(__name__)
    app.register_blueprint(account_bp)
    app.register_blueprint(seat_bp)  # ✅ 注册座位蓝图
    with app.app_context():
        init_db()
        init_seats()  # ✅ 初始化 seats 表
    return app
