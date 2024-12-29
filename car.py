from config import language, use_mistral, ollama_ip
from flask import Flask, render_template, request, jsonify, make_response
import requests
import time
import json
import os
from motor_control import move_car, gpio_cleanup
from llm import get_ollama_ip, execute_on_mistral, execute_on_ollama


app = Flask(__name__, static_folder='static')


# --- Endpoint for the movements ---
@app.route('/move', methods=['POST'])
def move():
    """
    Example:
      {
        "direction": "forward",
        "voltage": 6.0,
        "duration": 2.0
      }
    Possible directions:
      - "forward"
      - "backward"
      - "turn_left"
      - "turn_right"
      - "back_left"
      - "back_right"
    """
    data = request.get_json() or {}
    direction = data.get('direction', 'stop')
    voltage = data.get('voltage', 6.0)
    duration = data.get('duration', 1.0)
    if move_car(direction, voltage, duration):
        return jsonify({
            "status": "success",
            "message": f"Executed movement '{direction}' for {duration} seconds at {voltage}V"
        }), 200
    return jsonify({
        "status": "stopped",
        "message": "Invalid direction or 'stop' command"
    }), 400



# --- LLM call ---
@app.route('/llm', methods=['POST'])
def llm():
    message = request.form.get('message')
    if not message:
        return jsonify({"status": "error", "message": "No message provided"}), 400
    if use_mistral:
        return execute_on_mistral(message)
    return execute_on_ollama(message)


@app.route('/get_ollama_ip', methods=['GET'])
def get_ollama_ip_route():
    current_ip = get_ollama_ip()
    return jsonify({"status": "success", "ollama_ip": current_ip}), 200


@app.route('/set_ollama_ip', methods=['POST'])
def set_ollama_ip_route():
    data = request.get_json() or {}
    new_ip = data.get('ip', None)
    if new_ip:
        resp = make_response(jsonify({"status": "success", "message": "IP updated"}), 200)
        resp.set_cookie('ollama_ip', new_ip)
        set_ollama_ip(new_ip)
        return resp
    return jsonify({"status": "error", "message": "Invalid IP provided"}), 400


@app.route('/')
def index():
    # This is the UI for the car
    lng = "EN"
    if language == "HU":
        lng = language
    return render_template(f"index{lng}.html", ollama_ip=get_ollama_ip(), show_button=not use_mistral)


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=80)  # Port 80 requires root privileges!
    finally:
        gpio_cleanup()
