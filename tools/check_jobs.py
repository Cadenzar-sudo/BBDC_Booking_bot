import json
import threading
from shared import app, db
from models.user import User
from datetime import date,datetime
import logging
from tools.camp_slots import camp_slots

def check_jobs():
  with app.app_context():
    users = db.session.execute(db.select(User)).scalars().all()
    job_json = []
    for user in users:
      user_json = user.to_dict()
      user_json["proxies"] = json.loads(user.proxies.replace("'",'"'))
      user_json["start_times"] = json.loads(user.start_times.replace("'",'"'))
      user_json["target_months"] = json.loads(user.target_months.replace("'",'"'))
      job_json.append(user_json)
    for user in job_json:
      start_times = user["start_times"]
      username = user["username"]
      password = user["password"]
      description = user["description"]
      target_month_lst = user["target_months"]
      no_of_reloads = user["no_of_reloads"]
      reload_time = user["reload_time"]
      buffer = user["buffer"]
      proxy = user["proxies"]

      threads=[]
      for start_time in start_times:
        dt = datetime.combine(date.today(), datetime.strptime(start_time, "%H:%M").time())
        # check if start_time has started, if so autologin and start searching for slots
        if dt.replace(second=0, microsecond=0) == datetime.now().replace(second=0, microsecond=0):
          t = threading.Thread(target=camp_slots,args=(username,password,
                                                        description,target_month_lst,
                                                        no_of_reloads,reload_time,
                                                        buffer,proxy))
          threads.append(t)
      for thread in threads:
        thread.start()

                
def schedule_run():
    thread = threading.Timer(60.0,schedule_run)
    thread.start()
    try:
      check_jobs()
    except Exception as e:
      logging.info(e)
