from tools.skip_ui import get_slots
from tools.autologin import autologin
from tools.skip_ui import solve_capcha
from utils.notify import notify
from shared import app
import time
import logging
import random
def camp_slots(username,password,description,target_month_lst,no_of_reloads,reload_time,buffer,proxy):
      success = False
      for i in range(3):
        try:
          with app.app_context():
            login_result = autologin(username,password,description,proxy)
            success = True
            break
        except Exception as e:
          logging.critical(f"{e}")
          time.sleep(5) # try to wait for error to be over
      if success == False:
        raise Exception("Cannot login into account")
      
      if login_result == "reschedule the next slot finding":
        return None
      else:
        auth_token,jsession,bbdc_session = login_result
      reload_counter = 0
      while reload_counter < no_of_reloads:
            for i in range(36): # reload 36 times then take a 2 minute pause, if reloaded 270 times stop
              logging.info(reload_counter+1)
              if reload_counter >= no_of_reloads: break # break if reload counter above no of reloads
              target_month_lst_tmp = target_month_lst
              while len(target_month_lst_tmp) != 0: #if target month is inside lst, get that months slots
                time.sleep(reload_time + random.randint(0,3) + random.random())
                slots_lst,target_month_lst_tmp = get_slots(auth_token=auth_token,j_session_id=jsession,
                          bbdc_session=bbdc_session,
                          target_months=target_month_lst_tmp,proxy=proxy)
                if slots_lst == False:
                  notify(target_month_lst_tmp) #notify with error message sent
                  return "stop"
                reload_counter += 1
                logging.info((slots_lst,target_month_lst_tmp))
                if len(slots_lst) != 0: #check if slot was found, if so get capcha and autobook
                  # updated to start booking immediately once slot is found, do not check if other months are found
                  try:
                    response = solve_capcha(slots_lst,username,description,buffer,auth_token,jsession,bbdc_session,proxy)
                    if response == "stop":
                      return "stop"
                  except Exception as e:
                    logging.critical(e)

            logging.info("waiting 2 minutes")
            time.sleep(120 + random.randint(0,5) + random.random()) 
