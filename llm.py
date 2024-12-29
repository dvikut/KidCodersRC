from config import language, use_mistral, ollama_ip
import os
from mistralai import Mistral
import requests
from flask import jsonify
import json

previous_movements = []
if use_mistral:
    client = Mistral(api_key=os.environ.get('MISTRAL_API_KEY'))


def get_ollama_ip():
    return ollama_ip


def set_ollama_ip(ip):
    global ollama_ip
    ollama_ip = ip

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
    actual_movements = []
    previous_movements.append(movement_commands)
    for command in movement_commands:
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
