# seats.py
from flask import Blueprint, request, jsonify
import sqlite3
from datetime import datetime

DATABASE = "library.db"
seat_bp = Blueprint("seat", __name__)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ✅ 初始化座位表（函数名保持为 init_seats，与你 app.py 一致）
def init_seats():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seats (
            seat_id TEXT PRIMARY KEY,
            occupied_by TEXT,
            status TEXT,
            updated_at TEXT
        )
    """)
    # 初始化一些示例座位
    seats = ["T1", "T2", "T3", "T4", "T5", "B1", "B2", "B3", "B4"]
    for sid in seats:
        conn.execute("INSERT OR IGNORE INTO seats (seat_id, status) VALUES (?, '空闲')", (sid,))
    conn.commit()
    conn.close()


# ✅ 获取所有座位状态
@seat_bp.route("/seats", methods=["GET"])
def get_seats():
    conn = get_db()
    rows = conn.execute("SELECT * FROM seats").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ✅ 处理选座 / 暂离 / 退座操作
@seat_bp.route("/seat_action", methods=["POST"])
def seat_action():
    data = request.json
    student_id = data.get("student_id")
    seat_id = data.get("seat_id")
    action = data.get("action")

    conn = get_db()
    seat = conn.execute("SELECT * FROM seats WHERE seat_id=?", (seat_id,)).fetchone()

    if action == "选座":
        # 若座位被他人占用
        if seat and seat["occupied_by"] and seat["occupied_by"] != student_id:
            conn.close()
            return jsonify({"status": "error", "msg": "该座位已被他人占用"})
        # 若该用户已有座位
        existing = conn.execute(
            "SELECT seat_id FROM seats WHERE occupied_by=? AND status='使用中'",
            (student_id,)
        ).fetchone()
        if existing:
            conn.close()
            return jsonify({"status": "error", "msg": f"您已占用 {existing['seat_id']}，请先退座"})
        # 正常选座
        conn.execute(
            "UPDATE seats SET occupied_by=?, status='使用中', updated_at=? WHERE seat_id=?",
            (student_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), seat_id)
        )

    elif action == "退座":
        conn.execute(
            "UPDATE seats SET occupied_by=NULL, status='空闲', updated_at=? WHERE seat_id=? AND occupied_by=?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), seat_id, student_id)
        )

    elif action == "暂离":
        conn.execute(
            "UPDATE seats SET status='暂离', updated_at=? WHERE seat_id=? AND occupied_by=?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), seat_id, student_id)
        )

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "msg": f"{action}成功"})


# ✅ 重置座位（全部清空）
@seat_bp.route("/seats/reset", methods=["POST"])
def reset_seats():
    conn = get_db()
    conn.execute("UPDATE seats SET occupied_by=NULL, status='空闲'")
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "msg": "已重置所有座位"})

