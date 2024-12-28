import requests
import time

# This is an ugly but practical code

with open("toy_car.ip", "r") as ipfile:
    ip = ipfile.read().strip()
api_url = f"http://{ip}/move"


def call(command, duration: float):
    try:
        move_data = {
            "direction": command,
            "voltage": 6.0,
            "duration": duration
        }
        response = requests.post(api_url, json=move_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return False


def forward(duration=1.0):
    return call("forward", duration)


def left(duration=1.0):
    return call("turn_left", duration)


def right(duration=1.0):
    return call("turn_right", duration)


def backward(duration=1.0):
    return call("backward", duration)


def back_left(duration=1.0):
    return call("back_left", duration)


def back_right(duration=1.0):
    return call("back_right", duration)


def wait(duration=1.0):
    time.sleep(duration)
