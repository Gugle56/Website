from flask import Flask, render_template, request, redirect
import json
import os

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/slips'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

SLIP_FILE = "slip.json"

def load_slips():
    if not os.path.exists(SLIP_FILE): return []
    with open(SLIP_FILE, "r") as f: return json.load(f)

def save_slips(slips):
    with open(SLIP_FILE, "w") as f: json.dump(slips, f)

QUEUE_FILE = "queue.json"
RECENT_DONE_FILE = "recent_done.json"

def load_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE, "r") as f:
        return json.load(f)

def save_queue(queue):
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f)

def save_recent_done(user_id):
    with open(RECENT_DONE_FILE, "w") as f:
        json.dump({"id": user_id}, f)

def load_recent_done():
    if not os.path.exists(RECENT_DONE_FILE):
        return None
    with open(RECENT_DONE_FILE, "r") as f:
        data = json.load(f)
        return data.get("id")

def clear_recent_done():
    if os.path.exists(RECENT_DONE_FILE):
        os.remove(RECENT_DONE_FILE)

@app.route("/", methods=["GET", "POST"])
def index():
    queue = load_queue()
    user_id = request.remote_addr
    recent_done = load_recent_done()

    if request.method == "POST":
        name = request.form["name"]
        subject = request.form["subject"]
        description = request.form["description"]

        status = "doing" if not queue else "waiting"
        queue.append({
            "id": user_id,
            "name": name,
            "subject": subject,
            "description": description,
            "status": status
        })
        save_queue(queue)
        return redirect("/")

    # ตรวจสอบจากคิว
    for i, user in enumerate(queue):
        if user["id"] == user_id:
            return render_template("index.html", status=user["status"], position=i)

    # ถ้าถูกลบออกไปแล้วแต่เป็น recent_done
    if user_id == recent_done:
        clear_recent_done()
        return render_template("index.html", status="done")

    return render_template("index.html", status=None)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    queue = load_queue()
    if request.method == "POST" and queue:
        # ลบคนแรกทันที และจำ id ไว้แสดง "done"
        finished_user = queue.pop(0)
        save_recent_done(finished_user["id"])

        # คนต่อไปเป็น doing
        if queue:
            queue[0]["status"] = "doing"
        save_queue(queue)
        return redirect("/admin")

    return render_template("admin.html", queue=queue)

@app.route("/skip", methods=["GET", "POST"])
def skip():
    user_id = request.remote_addr
    queue = load_queue()

    if request.method == "POST":
        if 'slip' not in request.files:
            return "No file uploaded", 400
        slip = request.files['slip']
        if slip.filename == '':
            return "No selected file", 400

        # สร้างชื่อไฟล์ไม่ซ้ำ
        import uuid, os
        filename = str(uuid.uuid4()) + os.path.splitext(slip.filename)[1]
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        slip.save(path)

        # โหลด/บันทึกสลิปลง slip.json
        slips = load_slips()
        slips.append({"id": user_id, "file": filename})
        save_slips(slips)

        return "แจ้งโอนแล้ว! กรุณารอการตรวจสอบ"

    return render_template("skip.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)