import requests
from utils.capcha_solver import ocr_base64
from utils.notify import notify,wait_capcha
from shared import db
from models.user import User
import json
import logging

def get_cookies(proxy,cookies):
    bbdc_session = requests.sessions.Session()
    url = "https://booking.bbdc.sg/"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "dnt": "1",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    }
    
    response = bbdc_session.get(url, headers=headers,proxies=proxy,cookies=cookies)
    logging.info(response.cookies.get_dict())
    return (bbdc_session,response.cookies.get_dict())

def login_user(username,password,bbdc_session,proxy):
    url = "https://booking.bbdc.sg/bbdc-back-service/api/auth/checkIdAndPass"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://booking.bbdc.sg",
        "priority": "u=1, i",
        "referer": "https://booking.bbdc.sg/",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    }


    payload = {
        "userId": username,
        "userPass": password
    }

    response = bbdc_session.post(url, headers=headers, json=payload, proxies=proxy)

    logging.info(response.status_code)
    logging.info(response.json())
    return response.json()["success"]

def solve_login_capcha(username,password,bbdc_session,proxy):
    capcha_url = "https://booking.bbdc.sg/bbdc-back-service/api/auth/getLoginCaptchaImage"

    capcha_headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://booking.bbdc.sg",
        "priority": "u=1, i",
        "referer": "https://booking.bbdc.sg/",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    }

    capcha_payload = {}

    response = bbdc_session.post(capcha_url, headers=capcha_headers, json=capcha_payload, proxies=proxy)

    capcha_json = response.json()["data"]
    
    capcha,image_base64 = ocr_base64(capcha_json["image"])
    capcha_counter = 0

    while len(capcha) < 5 and capcha_counter < 3: # Get new capcha and solve again if capcha don't make sense
        response = bbdc_session.post(capcha_url, headers=capcha_headers, json=capcha_payload, proxies=proxy)
        capcha_json = response.json()["data"]
        capcha,image_base64 = ocr_base64(capcha_json["image"])
        capcha_counter += 1
    
    capcha_token = capcha_json["captchaToken"]
    verify_code_id = capcha_json["verifyCodeId"]
    retry_counter = 0
    
    login_url = "https://booking.bbdc.sg/bbdc-back-service/api/auth/login"

    login_headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "dnt": "1",
        "jsessionid": "", 
        "origin": "https://booking.bbdc.sg",
        "priority": "u=1, i",
        "referer": "https://booking.bbdc.sg/",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }

    login_payload = {
        "captchaToken": capcha_token,
        "verifyCodeId": verify_code_id,
        "verifyCodeValue": capcha,
        "userId": username,
        "userPass": password
    }

    response = bbdc_session.post(login_url, headers=login_headers, json=login_payload, proxies=proxy)
    capcha_counter = 0
    retry_counter = 0

    # checks if capcha is correct and retrieve auth-token

    while not response.json()["success"] and retry_counter <= 3: # if capcha fails more than 3 time msg user to solve capcha
      response = bbdc_session.post(capcha_url, headers=capcha_headers, json=capcha_payload, proxies=proxy)
      capcha_json = response.json()["data"]
      capcha,image_base64 = ocr_base64(capcha_json["image"])
      capcha_counter += 1
      
      login_payload["captchaToken"] = capcha_json["captchaToken"]
      login_payload["verifyCodeId"] = capcha_json["verifyCodeId"]
      login_payload["verifyCodeValue"] = capcha

      response = bbdc_session.post(login_url, headers=login_headers, json=login_payload, proxies=proxy)
      if response.json()["success"]: break #if login successful break
      retry_counter += 1

    if not response.json()["success"]: # if capcha was wrong 3 times get human to solve
        notify(f"capcha cannot be solved for {username}",image_base64)
        capcha = wait_capcha(username)
        if capcha == "expired": #if capcha was not given within 1.5mins get human to solve new capcha
          notify("Last capcha expired")
          response = bbdc_session.post(capcha_url, headers=capcha_headers, json=capcha_payload, proxies=proxy)
          capcha_base64 = response.json()["data"]["image"]
          notify("Solve new capcha",capcha_base64)
          capcha = wait_capcha(username)

          login_payload["captchaToken"] = capcha_json["captchaToken"]
          login_payload["verifyCodeId"] = capcha_json["verifyCodeId"]
          login_payload["verifyCodeValue"] = capcha

          response = bbdc_session.post(login_url, headers=login_headers, json=login_payload, proxies=proxy)
        elif capcha == "invalid": # if capcha was not given within 5 minutes, cancel login
          notify("reschedule the next slot finding")
          return None
        else: # if capcha was given within 30s use it
          login_payload["captchaToken"] = capcha_json["captchaToken"]
          login_payload["verifyCodeId"] = capcha_json["verifyCodeId"]
          login_payload["verifyCodeValue"] = capcha
          response = bbdc_session.post(login_url, headers=login_headers, json=login_payload, proxies=proxy)
               
    
    auth_token = response.json()["data"]["tokenContent"] # include in future request headers

    return auth_token

def get_jsession(auth_token,bbdc_session,proxy):
    url = "https://booking.bbdc.sg/bbdc-back-service/api/account/listAccountCourseType"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": auth_token,
        "content-type": "application/json",
        "dnt": "1",
        "jsessionid": "", 
        "origin": "https://booking.bbdc.sg",
        "priority": "u=1, i",
        "referer": "https://booking.bbdc.sg/",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }

    payload = {}

    response = bbdc_session.post(url, headers=headers, json=payload, proxies=proxy)

    logging.info(f"Response JSON:  {response.text}")
    jsession_json = response.json()
    jsession = jsession_json["data"]["activeCourseList"][0]["authToken"]
    return jsession


def autologin(username,password,description,proxy):
    user = db.session.get(User,username)
    if user.cookies:
        static_cookies = json.loads(user.cookies.replace("'",'"'))
        bbdc_session,cookies = get_cookies(proxy,static_cookies)
    else:
       static_cookies = None
       bbdc_session,cookies = get_cookies(proxy,{})
    authenticated = login_user(username,password,bbdc_session,proxy)
    user.cookies = str(cookies)
    db.session.commit()
    if not authenticated:
       notify(f"{description} was suspended, all jobs were cleared")
       user.start_times = json.dumps([])
       db.session.commit()
       return "reschedule the next slot finding"

    auth_token = solve_login_capcha(username,password,bbdc_session,proxy)
    if auth_token == None:
      return "reschedule the next slot finding"
    jsession = get_jsession(auth_token,bbdc_session,proxy)
    return [auth_token,jsession,bbdc_session]
