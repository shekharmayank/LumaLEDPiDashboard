import atexit
import json
import logging

from flask import Flask, render_template, request, redirect, url_for, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from config import DEVICE_CONFIG, SPI_CONFIG, ANIMATIONS
from models import (
    init_db,
    get_items,
    get_item,
    add_item,
    update_item,
    delete_item,
    reorder_items,
    get_todos,
    add_todo,
    toggle_todo,
    delete_todo,
    has_todo_in_playlist,
)
from display_engine import DisplayEngine

app = Flask(__name__)
engine = None


def create_device():
    from luma.led_matrix.device import max7219
    from luma.core.interface.serial import spi, noop

    serial = spi(port=SPI_CONFIG["port"], device=SPI_CONFIG["device"], gpio=noop())
    device = max7219(
        serial,
        cascaded=DEVICE_CONFIG["cascaded"],
        block_orientation=DEVICE_CONFIG["block_orientation"],
        blocks_arranged_in_reverse_order=DEVICE_CONFIG[
            "blocks_arranged_in_reverse_order"
        ],
    )
    device.contrast(DEVICE_CONFIG["contrast"])
    return device


def start_display():
    global engine
    try:
        device = create_device()
    except Exception as e:
        logging.error("Failed to create LED device: %s", e)
        device = None
    if device is not None:
        engine = DisplayEngine(device)
        engine.start()


def stop_display():
    global engine
    if engine is not None and engine.is_alive():
        engine.stop.set()
        engine.reload.set()
        engine.join(timeout=3)


@app.template_filter("item_label")
def item_label(item):
    t = item["type"]
    if t == "time":
        return "Time"
    if t == "date":
        return "Date"
    if t == "animation":
        name = item["config"].get("name", "")
        return f"Animation: {name}"
    if t == "message":
        text = item["config"].get("text", "")
        if len(text) > 20:
            text = text[:20] + "..."
        return f'Message: "{text}"'
    if t == "todo":
        return "Todo List"
    return t


@app.route("/")
def index():
    items = get_items()
    return render_template("index.html", items=items, anims=ANIMATIONS)


@app.route("/item/new", methods=["GET", "POST"])
def item_new():
    if request.method == "POST":
        type_ = request.form["type"]
        config = {}
        duration = request.form.get("duration", type=int)
        if type_ == "animation":
            config["name"] = request.form["name"]
        elif type_ == "message":
            config["text"] = request.form["text"]
        if type_ == "todo":
            duration = None
        add_item(type_, config, duration)
        if engine is not None:
            engine.reload.set()
        return redirect(url_for("index"))
    return render_template("item_form.html", item=None, anims=ANIMATIONS)


@app.route("/item/<int:item_id>/edit", methods=["GET", "POST"])
def item_edit(item_id):
    item = get_item(item_id)
    if item is None:
        return redirect(url_for("index"))
    if request.method == "POST":
        type_ = request.form["type"]
        config = {}
        duration = request.form.get("duration", type=int)
        if type_ == "animation":
            config["name"] = request.form["name"]
        elif type_ == "message":
            config["text"] = request.form["text"]
        if type_ == "todo":
            duration = None
        update_item(item_id, type_, config, duration)
        if engine is not None:
            engine.reload.set()
        return redirect(url_for("index"))
    return render_template("item_form.html", item=item, anims=ANIMATIONS)


@app.route("/item/<int:item_id>/delete", methods=["POST"])
def item_delete(item_id):
    delete_item(item_id)
    if engine is not None:
        engine.reload.set()
    return redirect(url_for("index"))


@app.route("/api/reorder", methods=["POST"])
def api_reorder():
    data = request.get_json()
    item_ids = data.get("item_ids", [])
    reorder_items(item_ids)
    if engine is not None:
        engine.reload.set()
    return jsonify({"ok": True})


@app.route("/todos")
def todos():
    items = get_todos()
    return render_template("todos.html", items=items)


@app.route("/api/todos/add", methods=["POST"])
def api_todos_add():
    data = request.get_json()
    text = data.get("text", "").strip()
    if text:
        add_todo(text)
        if engine is not None and has_todo_in_playlist():
            engine.reload.set()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "empty text"}), 400


@app.route("/api/todos/<int:todo_id>/toggle", methods=["POST"])
def api_todos_toggle(todo_id):
    toggle_todo(todo_id)
    if engine is not None and has_todo_in_playlist():
        engine.reload.set()
    return jsonify({"ok": True})


@app.route("/api/todos/<int:todo_id>/delete", methods=["POST"])
def api_todos_delete(todo_id):
    delete_todo(todo_id)
    if engine is not None and has_todo_in_playlist():
        engine.reload.set()
    return jsonify({"ok": True})


@app.route("/api/status")
def api_status():
    return jsonify({
        "engine_alive": engine is not None and engine.is_alive(),
    })


def main():
    init_db()
    start_display()
    atexit.register(stop_display)
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
