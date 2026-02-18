from flask import request,jsonify,render_template
from tools.check_jobs import schedule_run
from models.user import User
from flask_cors import CORS
from utils.run_once_with_sentinel import run_once_with_sentinel
from shared import app,db
import json
import logging
import threading
import datetime


CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
FILE_LOCK = threading.Lock()

logging.basicConfig(filename='app.log', level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')

#TODO add feature to get capcha in advance from other account
@app.route("/api/update",methods=["POST"])
def update_jobs():
  try:
    jobs_lst = request.get_json()
    with FILE_LOCK: #ensure only 1 thread accessing file at a time
      with open("proxies.json","r") as f:
        proxies = json.load(f)

    no_of_proxies = len(proxies)
    proxy_selector = 0
    users_lst = db.session.execute(db.select(User)).scalars().all()
    created_users_lst = []

    for job in jobs_lst: #override old jobs because ui will automatically include old jobs inside
      proxy = proxies[proxy_selector] # assign diffrent proxy to diffrent users
      existing_user = db.session.get(User,job["username"])
      if existing_user:
        user = existing_user
        created_users_lst.append(user)
      else:
        user = User(username=job["username"])

      user.password = job["password"]
      user.proxies = f"{proxy}"
      user.start_times = f'{job["start_times"]}'
      user.target_months = f'{job["target_months"]}'
      user.description = job["description"]
      user.buffer = job["buffer"]
      user.reload_time = job["reload_time"]
      user.no_of_reloads = job["no_of_reloads"]
      proxy_selector += 1
      if proxy_selector >= no_of_proxies: #if all proxies have been assigned, assign proxies multiple times
        proxy_selector = 0
      
      if not existing_user:
        db.session.add(user)
    
    for user in users_lst:
      if user not in created_users_lst:
        db.session.delete(user) #delete user if they were deleted in ui
    db.session.commit()

    return jsonify({"response":"updated"})
  except Exception as e:
    logging.info(e)
    return jsonify({"response":"Internal Server Error"})

@app.route("/api/send_otp",methods=["POST"])
def send_otp():
    username = request.form.get("username")
    otp = request.form.get("otp")
    user = db.session.get(User, username)

    if not username or not otp:
       return jsonify({"response":"missing username or otp"})
    elif not user:
       return jsonify({"response":"Invalid username"})
    
    user.otp = otp
    user.otp_exp = datetime.datetime.now() + datetime.timedelta(minutes=3)
    db.session.commit()

    return jsonify({"response":"otp updated successfully"})
    

@app.route("/",methods=["GET"])
def dashboard():
    users = db.session.execute(db.select(User)).scalars().all()
    jobs_json = []
    for user in users:
      user.proxies = json.loads(user.proxies.replace("'",'"'))
      user.start_times = json.loads(user.start_times.replace("'",'"'))
      user.target_months = json.loads(user.target_months.replace("'",'"'))
      user = user.to_dict()
      jobs_json.append(user)
    return render_template("dashboard.html",jobs_json=jobs_json)

run_once_with_sentinel(schedule_run)