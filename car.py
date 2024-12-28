from flask import Flask, render_template, request, jsonify, make_response
import requests
import RPi.GPIO as GPIO
import time
import json
import os
from mistralai import Mistral

language = "EN"  # "EN" / "HU"
ollama_ip = "192.168.0.221"  # For language control only
use_mistral = True # This requires the API KEY in 'MISTRAL_API_KEY' environment variable

previous_movements = []

app = Flask(__name__, static_folder='static')

# --- GPIO Pin Assignment ---
# Motor A (Steering)
ENA = 17  # Speed control pin for motor A
IN1 = 27  # Direction pin
IN2 = 22  # Direction pin

# Motor B (Drive)
ENB = 18  # Speed control pin for motor B
IN3 = 23  # Direction pin
IN4 = 24  # Direction pin

# --- GPIO Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)

# --- PWM Setup ---
pwm_A = GPIO.PWM(ENA, 1000)  # Frequency = 1000 Hz
pwm_B = GPIO.PWM(ENB, 1000)

pwm_A.start(0)
pwm_B.start(0)


def get_ollama_ip():
    return ollama_ip


def set_ollama_ip(ip):
    global ollama_ip
    ollama_ip = ip


def set_motor_voltage(motor: str, voltage: float):
    """
    Sets the PWM duty cycle for the specified motor (A or B) based on the voltage.
    Motor A (steering) always operates at 6V.
    """
    max_voltage = 7.6      # The LiPo battery voltage is around 7.4-7.6 V
    max_safe_voltage = 6.0 # The car was designed for four AA batteries

    if motor == 'A' and voltage > 0:
        voltage = max_safe_voltage
    else:
        voltage = min(voltage, max_safe_voltage)

    duty_cycle = (voltage / max_voltage) * 100.0
    if motor == 'A':
        pwm_A.ChangeDutyCycle(duty_cycle)
    elif motor == 'B':
        pwm_B.ChangeDutyCycle(duty_cycle)


def set_motor_direction(motor: str, direction: str):
    """
    Motor A: 'left', 'right', 'stop'
    Motor B: 'forward', 'backward', 'stop'
    """
    if motor == 'A':  # Steering
        if direction == 'right':
            GPIO.output(IN1, GPIO.HIGH)
            GPIO.output(IN2, GPIO.LOW)
        elif direction == 'left':
            GPIO.output(IN1, GPIO.LOW)
            GPIO.output(IN2, GPIO.HIGH)
        else:
            # stop
            GPIO.output(IN1, GPIO.LOW)
            GPIO.output(IN2, GPIO.LOW)

    elif motor == 'B':  # Drive
        if direction == 'forward':
            GPIO.output(IN3, GPIO.HIGH)
            GPIO.output(IN4, GPIO.LOW)
        elif direction == 'backward':
            GPIO.output(IN3, GPIO.LOW)
            GPIO.output(IN4, GPIO.HIGH)
        else:
            # stop
            GPIO.output(IN3, GPIO.LOW)
            GPIO.output(IN4, GPIO.LOW)


def stop_all_motors():
    pwm_A.ChangeDutyCycle(0)
    pwm_B.ChangeDutyCycle(0)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)


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
      - "forward" (előre)
      - "backward" (hátra)
      - "turn_left" (balra előre)
      - "turn_right" (jobbra előre)
      - "back_left" (hátra-balra)
      - "back_right" (hátra-jobbra)
      - "stop" (leáll)
    """
    data = request.get_json() or {}
    direction = data.get('direction', 'stop')
    voltage = data.get('voltage', 6.0)
    duration = data.get('duration', 1.0)

    if direction == 'forward':
        set_motor_voltage('B', voltage)
        set_motor_direction('B', 'forward')
    elif direction == 'backward':
        set_motor_voltage('B', voltage)
        set_motor_direction('B', 'backward')
    elif direction == 'turn_left':
        set_motor_voltage('B', voltage)
        set_motor_voltage('A', 6.0)
        set_motor_direction('B', 'forward')
        set_motor_direction('A', 'left')
    elif direction == 'turn_right':
        set_motor_voltage('B', voltage)
        set_motor_voltage('A', 6.0)
        set_motor_direction('B', 'forward')
        set_motor_direction('A', 'right')
    elif direction == 'back_left':
        set_motor_voltage('B', voltage)
        set_motor_voltage('A', 6.0)
        set_motor_direction('B', 'backward')
        set_motor_direction('A', 'left')
    elif direction == 'back_right':
        set_motor_voltage('B', voltage)
        set_motor_voltage('A', 6.0)
        set_motor_direction('B', 'backward')
        set_motor_direction('A', 'right')
    else:
        # invalid direction or 'stop'
        stop_all_motors()
        return jsonify({
            "status": "stopped",
            "message": "Invalid direction or 'stop' command"
        }), 400

    time.sleep(duration)
    stop_all_motors()

    return jsonify({
        "status": "success",
        "message": f"Executed movement '{direction}' for {duration} seconds at {voltage}V"
    }), 200


def get_previous_movements():
    ret = ""
    if len(previous_movements) > 0:
        for movements in previous_movements:
            ret += ", ".join(movements) + "\n\n"
        return ret
    if language == "HU":
        return "Eddig nem mozogtál."
    return "No movements yet."


def get_prompt(msg):
    if language == "HU":
        return f"Egy kis távirányítós autó vagy. Kérlek mozogj a felhasználó kívánsága szerint, " \
                "amit úgy tudsz megtenni, hogy a mozgásokat felsorolod egymás után.\n\n " \
                f"Az eddigi mozgásaid:\n{get_previous_movements()}\n\n\n" \
                "Ezek a lehetséges mozgások: 'előre', 'balra-előre', 'jobbra-előre', 'hátra', " \
                "'hátra-balra', 'hátra-jobbra'. Egy JSON array-ban válaszolja tripla json aposztrofok nélkül, kizárólag a lehetséges mozgásokat felsorolva.\n" \
                f"A felhasználó óhaja: {msg}"
    else:
        return f"You are a small remote-controlled car. Please move according to the user's instructions, " \
                "which you can do by listing the movements one after the other.\n\n" \
                f"Your previous movements were:\n{get_previous_movements()}\n\n\n" \
                "These are the possible movements: 'forward', 'turn_left', 'turn_right', 'backward', " \
                "'backward-left', 'backward-right'. Reply in a JSON array without the json triple quotes strictly with the possible movements.\n" \
                f"The user's request: {msg}"


def get_instructions():
    if language == "HU":
        return [
            "előre",
            "balra-előre",
            "jobbra-előre",
            "hátra",
            "hátra-balra",
            "hátra-jobbra"
        ]
    else:
        return [
            "forward",
            "turn_left",
            "turn_right",
            "backward",
            "backward-left",
            "backward-right"
        ]


def command2direction(command):
    if language == "HU":
        if command in ("előre", "elore"):
            return"forward"
        elif command in ("hátra", "hatra"):
            return"backward"
        elif command in ("balra-előre", "balra-elore", "balra", "elore-balra", "előre-balra"):
            return"turn_left"
        elif command in ("jobbra-előre", "jobbra-elore", "jobbra", "elore-jobbra", "előre-jobbra"):
            return"turn_right"
        elif command in ("hátra-balra", "hatra-balra", "balra-hatra", "balra-hátra"):
            return"back_left"
        elif command in ("hátra-jobbra", "hatra-jobbra", "jobbra-hátra", "hátra-jobbra"):
            return"back_right"
    else:
        if command in get_instructions():
            return command
    return "stop"

def execute_commands(movement_commands):
    app.logger.info(f"Executing movements: {movement_commands}")
    actual_movements = []
    previous_movements.append(movement_commands)
    for command in movement_commands:
        app.logger.info(f"Movement command: {command}")
        direction_for_move = command2direction(command)
        actual_movements.append(direction_for_move)
        move_data = {
            "direction": direction_for_move,
            "voltage": 6.0,
            "duration": 1.0
        }
        requests.post("http://localhost/move", json=move_data)
    return jsonify({"status": "success", "message": f"Executed all movement commands {movement_commands}. Actaul movements: {actual_movements}"})


def execute_on_ollama(message):
    ip = request.cookies.get('ollama_ip', default="192.168.0.221")
    api_url = f"http://{ip}:11434/api/generate"
    headers = {'Content-Type': 'application/json'}
    request_data = {
        "model": "llama3.2",
        "prompt": get_prompt(message),
        "stream": False,
        "format": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": get_instructions()
            }
        }
    }
    try:
        response = requests.post(api_url, json=request_data, headers=headers)
        if response.status_code == 200:
            api_response = response.json()
            movement_commands = json.loads(api_response.get("response", []))
            return execute_commands(movement_commands)
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to send request: {response.status_code}"
            }), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def execute_on_mistral(message):
    # the response_format is useless here
    prompt = get_prompt(message)
    print(prompt)
    chat_response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    print(chat_response.choices[0].message.content)
    movement_commands = json.loads(chat_response.choices[0].message.content)
    return execute_commands(movement_commands)


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
    if use_mistral:
        client = Mistral(api_key=os.environ.get('MISTRAL_API_KEY'))
    try:
        app.run(host='0.0.0.0', port=80)  # Port 80 requires root privileges!
    finally:
        pwm_A.stop()
        pwm_B.stop()
        GPIO.cleanup()
