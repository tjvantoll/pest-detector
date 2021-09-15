import keys
import os
import notecard
from pathlib import Path
from periphery import I2C
import picamera
import RPi.GPIO as GPIO
from run_tf_detector import load_and_run_detector
from run_tf_detector_batch import load_and_run_detector_batch, write_results_to_file
import time

notehub_uid = 'com.blues.tvantoll:pestcontrol'
port = I2C("/dev/i2c-1")
card = notecard.OpenI2C(port, 0, 0)

model = './md_v4.1.0'
model = ''.join([str(f) for f in Path('.').rglob('*.pb')])

pir_sensor_pin = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(pir_sensor_pin, GPIO.IN)

def process_image(file_name):
  output_path = './output.json'
  results = load_and_run_detector_batch(
    model_file=model,
    image_file_names=[file_name],
    checkpoint_path=output_path,
    confidence_threshold=0.6,
  )
  write_results_to_file(results, output_path)
  return results

def draw_detection_boxes(file_name):
  load_and_run_detector(
    model,
    [file_name],
    str(Path('./images'))
  )

def get_image_name():
  path, dirs, files = next(os.walk('images'))
  file_count = len(files)
  return 'images/' + str(file_count + 1) + '.jpg'

def take_picture():
  camera = picamera.PiCamera()
  camera.resolution = (400, 400)
  camera.start_preview()
  time.sleep(2)
  camera.rotation = 90
  image_name = get_image_name()
  camera.capture(image_name)
  camera.stop_preview()
  camera.close()
  return image_name

def init_notecard():
  req = {"req": "hub.set"}
  req["product"] = notehub_uid
  req["mode"] = "continuous"
  req["sync"] = True
  res = card.Transaction(req)
  print(res)

def send_to_notehub():
  req = {"req": "note.add"}
  req["file"] = "twilio.qo"
  req["sync"] = True
  req["body"] = {
    "body": "Spotted an animal!",
    "from": keys.sms_from,
    "to": keys.sms_to,
  }
  res = card.Transaction(req)
  print(res)

def is_animal_image(ml_result):
  for detection in ml_result['detections']:
    if detection['category'] == '1':
      return True
  return False

def main():
  init_notecard()
  while True:
    sensor_state = GPIO.input(pir_sensor_pin)
    if sensor_state == GPIO.HIGH:
      print('Motion detected')
      image_name = take_picture()
      ml_result = process_image(image_name)[0]
      if is_animal_image(ml_result):
        print('Animal detected!')
        send_to_notehub()
      else:
        print('No animal detected')
        os.remove(image_name)

    time.sleep(5)

main()
