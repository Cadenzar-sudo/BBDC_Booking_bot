import requests
from io import BytesIO
import datetime
from datetime import timedelta
import json
import base64
from dotenv import load_dotenv
import os
import time
import logging

def fetch_with_manual_retry(url, retries=3,files=None,data=None):
    for i in range(retries):
      try:
        if files==None and data==None:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response
        else:
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            return response
        
      except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
        logging.error(f"Attempt {i+1} failed: {e}")
        if i < retries - 1:
          time.sleep(2) # Wait before retrying
        else:
          logging.critical("All retry attempts failed.")
          return None

load_dotenv()

def notify(message,image_base64=None,chat_id=None):
  TOKEN = os.getenv("TELEGRAM_TOKEN")
  if not chat_id: # use admin chat_id by default if chat_id not defined
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

  if image_base64 == None:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    fetch_with_manual_retry(url)
  else:
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    image_base64 = image_base64.replace("data:image/png;base64,","").strip()
    image_bytes = base64.b64decode(image_base64)
    image_file = BytesIO(image_bytes)
    files = {"photo": image_file}
    data = {"chat_id": chat_id, "caption": message}
    fetch_with_manual_retry(url=url,files=files,data=data)

def wait_capcha(username):
  TOKEN = os.getenv("TELEGRAM_TOKEN")
  url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
  with open("offset.json","r") as f:
    offset = json.load(f)["offset"]
  
  start_dt = datetime.datetime.now()
  while True:
    if (start_dt + timedelta(minutes=30)) < datetime.datetime.now(): # stop loop if 
      return "invalid"
    params = {"timeout": 100}  # Long polling
    if offset:
        params["offset"] = offset

    response = requests.get(url, params=params)
    update = response.json()
    if update["result"]:
      capcha = update["result"][0]["message"]["text"]
      received_time = update["result"][0]["message"]["date"]
      sender = update["result"][0]["message"]["from"]["username"]

      offset = update["result"][0]["update_id"] + 1  # Avoid processing same update again
      with open("offset.json","w") as f:
        json.dump({"offset":offset},f)


      dt = datetime.datetime.fromtimestamp(received_time)
      if sender != "Cadenzarz" or username not in capcha: #ignore if username not in capcha or sender is incorrect
        pass
      elif dt > (datetime.datetime.now() + timedelta(minutes=1.5)) and dt < (datetime.datetime.now() + timedelta(minutes=5)):
        return "expired"
      elif dt > (datetime.datetime.now() + timedelta(minutes=5)):
        return "invalid"
      else:
        return capcha.replace(username,"").strip()
