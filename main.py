# https://www.hackster.io/rob-lauer/remote-birding-with-tensorflow-lite-and-raspberry-pi-8c4fcc
# https://towardsdatascience.com/detecting-animals-in-the-backyard-practical-application-of-deep-learning-c030d3263ba8
# https://github.com/microsoft/CameraTraps
# https://github.com/dddjjjbbb/Grunz/blob/main/main.py
import keys
import json
import os
import notecard
from pathlib import Path
from periphery import I2C
import picamera
import time
from run_tf_detector import load_and_run_detector
from run_tf_detector_batch import load_and_run_detector_batch, write_results_to_file

notehub_uid = 'com.blues.tvantoll:pestcontrol'
port = I2C("/dev/i2c-1")
card = notecard.OpenI2C(port, 0, 0)

model = './md_v4.1.0'
model = ''.join([str(f) for f in Path('.').rglob('*.pb')])

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

def process_single_image(file_name):
  load_and_run_detector(
    model,
    [file_name],
    str(Path('./images'))
  )

def get_image_name():
  path, dirs, files = next(os.walk("images"))
  file_count = len(files)
  return 'images/' + str(file_count + 1) + '.jpg'

def take_picture():
  camera = picamera.PiCamera()
  camera.resolution = (500, 500)
  camera.start_preview()
  time.sleep(2)
  camera.rotation = 180
  image_name = get_image_name()
  camera.capture(image_name)
  camera.stop_preview()
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

# init_notecard()

def main():
  image_name = take_picture()
  ml_result = process_image(image_name)[0]
  if is_animal_image(ml_result):
    print('Animal!')
    send_to_notehub(ml_result['confidence'])
  else:
    os.remove(image_name)
