from config import ENA, IN1, IN2, ENB, IN3, IN4
import RPi.GPIO as GPIO
import time


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


def move_car(direction, voltage, duration):
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
        return False
    time.sleep(duration)
    stop_all_motors()
    return True


def stop_all_motors():
    pwm_A.ChangeDutyCycle(0)
    pwm_B.ChangeDutyCycle(0)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    
def gpio_cleanup():
    pwm_A.stop()
    pwm_B.stop()
    GPIO.cleanup()

