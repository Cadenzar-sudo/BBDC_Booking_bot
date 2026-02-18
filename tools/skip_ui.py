import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
import logging
import pytz
from datetime import datetime,timedelta,time
from utils.notify import notify,wait_capcha
from utils.capcha_solver import ocr_base64

def get_slots(auth_token,j_session_id,bbdc_session,target_months,proxy):

    url = "https://booking.bbdc.sg/bbdc-back-service/api/booking/c3practical/listC3PracticalSlotReleased"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": auth_token,
        "content-type": "application/json",
        "dnt": "1",
        "jsessionid": j_session_id,
        "origin": "https://booking.bbdc.sg",
        "priority": "u=1, i",
        "referer": "https://booking.bbdc.sg/",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    }

    cookies = {"bbdc-token": auth_token}

    data = {
        "courseType": "3C",
        "insInstructorId": "",
        "releasedSlotMonth": f"{target_months[0]}", #only get first month in lst slot
        "stageSubDesc": "Practical Lesson",
        "subVehicleType": None,
        "subStageSubNo": None
    }

    try:
        response = bbdc_session.post(url, headers=headers, cookies=cookies, json=data, proxies=proxy)
        slots_json = response.json()
    except ValueError:
        logging.info(f"Failed JSON: {response.text}")
        return [[],target_months]
    
    except ConnectionError:
        logging.info("Network connection failed (server down, DNS error, etc.)")
        return [[],target_months]

    except Timeout:
        logging.info("⏳ Request timed out")
        return [[],target_months]

    except requests.exceptions.HTTPError as e:
        logging.info(f"HTTP error: {e}")
        return [[],target_months]

    except RequestException as e:
        logging.info(f"General error: {e}")
        return [[],target_months]

    target_month_lst = []
    target_inside = False
    
    try:
      months_avaliable = slots_json["data"]["releasedSlotMonthList"]
      logging.info(months_avaliable)
    except KeyError as e:
      logging.info(e)
      logging.info(slots_json)
      if "message" in slots_json:
        if "The previous session has expired." in slots_json["message"]:
          return [False,"session expired"]
      return [[],target_months]


    for month in target_months:
       # use to rerun the function to get the other target month slot no
       for month_slot in months_avaliable:
          if month in month_slot["slotMonthYm"] and month != target_months[0]:
            target_month_lst.append(month)
          if target_months[0] in month_slot["slotMonthYm"]: #check if target month is inside slots retrieved
             target_inside = True
    
    # check if first target month is inside lst, if not return empty lst
    if not target_inside:
       return [[],target_month_lst]
             
    
    slots_dict = slots_json["data"]["releasedSlotListGroupByDay"]
    slots_info = []
    if not slots_dict: #if slot info is empty (false positive api)
      return [[],target_month_lst]
  
    for day in slots_dict:
      slots_lst = slots_dict[day]
      for slot_session in range(len(slots_lst)):
        slots_info.append({"slotId":slots_lst[slot_session]["slotId"],
                           "slotRefDate":slots_lst[slot_session]["slotRefDate"],
                           "start_time":slots_lst[slot_session]["startTime"],
                           "end_time":slots_lst[slot_session]["endTime"],
                           "slotIdEnc":slots_lst[slot_session]["slotIdEnc"],
                           "bookingProgressEnc":slots_lst[slot_session]["bookingProgressEnc"]})
    return [slots_info,target_month_lst]
    
def get_capcha(auth_token,j_session_id,bbdc_session,proxy):
    url = "https://booking.bbdc.sg/bbdc-back-service/api/booking/manage/getCaptchaImage"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": auth_token,
        "jsessionid": j_session_id,
        "origin": "https://booking.bbdc.sg",
        "referer": "https://booking.bbdc.sg/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }

    cookies = {"bbdc-token": auth_token}
    got_capcha = False
    try_counter = 0

    # Send GET request
    while not got_capcha and try_counter < 3:
      try:
        response = bbdc_session.post(url, headers=headers, cookies=cookies, proxies=proxy)
        got_capcha = True
      except:
        logging.info("Get Capcha again due to error")
        try_counter += 1
         

    return response.json()

def book_slots(auth_token,j_session_id,capcha,capcha_token,capcha_verify_id,slots_lst,bbdc_session,proxy,course_type):
    url = "https://booking.bbdc.sg/bbdc-back-service/api/booking/c3practical/callBookC3PracticalSlot"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": auth_token,
        "content-type": "application/json",
        "dnt": "1",
        "jsessionid": j_session_id,
        "origin": "https://booking.bbdc.sg",
        "priority": "u=1, i",
        "referer": "https://booking.bbdc.sg/",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }


    cookies = {"bbdc-token": auth_token}

    slot_id_lst = []
    encrypted_slot_lst = []
    for slot in slots_lst: 
      slot_id_lst.append(slot["slotId"])
      encrypted_slot_lst.append({"slotIdEnc":slot["slotIdEnc"],
                                 "bookingProgressEnc":slot["bookingProgressEnc"]})

    json_data = {
        "verifyCodeId": capcha_verify_id,
        "verifyCodeValue": capcha,
        "captchaToken": capcha_token,
        "courseType": course_type,
        "slotIdList": slot_id_lst,
        "encryptSlotList": encrypted_slot_lst,
        "insInstructorId": "",
        "subVehicleType": None,
        "instructorType": ""
    }

    booked_slot = False
    try_counter = 0
    
    while not booked_slot and try_counter < 3:
      try:
        response = bbdc_session.post(url, headers=headers, cookies=cookies, json=json_data, proxies=proxy)
        booked_slot = True
      except:
        logging.info("Attempting to book slot again")
        try_counter += 1

    return response.json()

def solve_capcha(slots_lst,username,description,buffer,auth_token,jsession,bbdc_session,proxy):
    tmp = []
    for slot in slots_lst:
      # 1. Setup Timezones
      sg_timezone = pytz.timezone("Asia/Singapore")
      now_sg = datetime.now(sg_timezone) # Get current time ALREADY localized to SG

      # 2. Parse the Slot
      slot_datetime_str = f'{slot["slotRefDate"].replace("00:00:00","").strip()} {slot["start_time"]}'
      dt_naive = datetime.strptime(slot_datetime_str, "%Y-%m-%d %H:%M")

      # Localize the parsed time (assuming the input string is meant to be SG time)
      dt_sg = sg_timezone.localize(dt_naive)

      # 3. Filter Logic
      # Check if slot is within the buffer period
      if dt_sg >= (now_sg + timedelta(minutes=buffer)):
          
          # Specific logic for Chee Heng
          if username == "525E03042006":
              course_type = "3A"
              is_weekend = dt_sg.weekday() in [5, 6] # Sat, Sun
              is_friday_evening = (dt_sg.weekday() == 4 and dt_sg.time() >= time(19, 0))
              
              if is_weekend or is_friday_evening:
                  tmp.append(slot)
                  
          # Logic for everyone else
          else:
              tmp.append(slot)
              course_type = "3C"

    slots_lst = tmp
    capcha_counter = 0
    solved_capcha = False

    while capcha_counter <= 5 and solved_capcha == False: # Get new capcha and solve again if capcha is invalid
        capcha_json = get_capcha(auth_token=auth_token,j_session_id=jsession,
                bbdc_session=bbdc_session,proxy=proxy) # get capcha
        
        capcha_img = capcha_json["data"]["image"]
        capcha_token = capcha_json["data"]["captchaToken"]
        capcha_verify_id = capcha_json["data"]["verifyCodeId"]
        capcha,image_base64 = ocr_base64(capcha_img)
        logging.info(f"attempting to use capcha {capcha}")
        # notify(f"attempting to use {capcha} for {description}",image_base64)
        response = book_slots(auth_token=auth_token,j_session_id=jsession,
                            capcha=capcha,capcha_token=capcha_token,
                            capcha_verify_id=capcha_verify_id,slots_lst=slots_lst,
                            bbdc_session=bbdc_session,proxy=proxy,course_type=course_type)
        logging.info(response)
        
        if response["success"]:# notify user if slot booked, if insufficient money stop job
          solved_capcha = True # Stop loops as capcha was correct
          slots_lst = response["data"]["bookedPracticalSlotList"]
          logging.info(response)
          for slot_info_json in slots_lst:
            if slot_info_json["success"]:
              slot_datetime_str = f"{slot_info_json['slotRefDate']} {slot_info_json['startTime']}-{slot_info_json['endTime']}"
              notify(f"{slot_datetime_str} was booked for {description}")
            elif "insufficient fund" in slot_info_json["message"]:
              notify(f"low funds for {description}")
              return "stop" # break if out of money
        else: # retry and get human to solve if needed
          logging.info(response)
          capcha_counter += 1

    if not solved_capcha: #if cannot solve get human to solve
      notify(f"capcha cannot be solved for {description} ({username})",image_base64)
      capcha = wait_capcha(username)
      if capcha == "expired": #if capcha was not given within 1.5mins get human to solve new capcha
        notify("Last capcha expired")
        capcha_json = get_capcha(auth_token=auth_token,j_session_id=jsession,
                                bbdc_session=bbdc_session,proxy=proxy) # get capcha
        capcha_img = capcha_json["data"]["image"]
        notify("Solve new capcha",capcha_img)
        capcha = wait_capcha(username)
        capcha_token = capcha_json["data"]["captchaToken"]
        capcha_verify_id = capcha_json["data"]["verifyCodeId"]
        response = book_slots(auth_token=auth_token,j_session_id=jsession,
                            capcha=capcha,capcha_token=capcha_token,
                            capcha_verify_id=capcha_verify_id,slots_lst=slots_lst,
                            bbdc_session=bbdc_session,proxy=proxy,course_type=course_type)
        if response["success"]:# notify user if slot booked, if insufficient money stop job
          solved_capcha = True # Stop loops as capcha was correct
          slots_lst = response["data"]["bookedPracticalSlotList"]
          logging.info(response)
          for slot_info_json in slots_lst:
            if slot_info_json["success"]:
              slot_datetime_str = f"{slot_info_json['slotRefDate']} {slot_info_json['startTime']}-{slot_info_json['endTime']}"
              notify(f"{slot_datetime_str} was booked for {description}")
            elif "insufficient fund" in slot_info_json["message"]:
              notify(f"low funds for {description}")
              return "stop" # break if out of money
      elif capcha == "invalid": # if capcha was not given within 5 minutes, cancel booking
        notify("capcha not answered in time, booking cancelled")
      else: # if capcha was given within 30s use it
        capcha_token = capcha_json["data"]["captchaToken"]
        capcha_verify_id = capcha_json["data"]["verifyCodeId"]
        response = book_slots(auth_token=auth_token,j_session_id=jsession,
                            capcha=capcha,capcha_token=capcha_token,
                            capcha_verify_id=capcha_verify_id,slots_lst=slots_lst,
                            bbdc_session=bbdc_session,proxy=proxy,course_type=course_type)
        if response["success"]:# notify user if slot booked, if insufficient money stop job
          solved_capcha = True # Stop loops as capcha was correct
          slots_lst = response["data"]["bookedPracticalSlotList"]
          logging.info(response)
          for slot_info_json in slots_lst:
            if slot_info_json["success"]:
              slot_datetime_str = f"{slot_info_json['slotRefDate']} {slot_info_json['startTime']}-{slot_info_json['endTime']}"
              notify(f"{slot_datetime_str} was booked for {description}")
            elif "insufficient fund" in slot_info_json["message"]:
              notify(f"low funds for {description}")
              return "stop" # break if out of money
    return


