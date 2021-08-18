import board
import digitalio
import time

pir_sensor = digitalio.DigitalInOut(board.D18)
pir_sensor.direction = digitalio.Direction.INPUT

while True:
  time.sleep(1)
  
  if pir_sensor.value:
    print("yes!")
  else:
    print("no!")