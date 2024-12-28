
from toy_car_commands import forward, backward, right, left, back_left, back_right, wait

# All commands are visible above, and you can specify seconds as a parameter if 1 is not suitable
# Below is the playground

forward()
left()
for _ in range(2):
    backward()
    forward()
wait(1.5)
backward(2)

