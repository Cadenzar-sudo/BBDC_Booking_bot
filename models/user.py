from shared import db

class User(db.Model):
    username = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(20), nullable=False)
    proxies = db.Column(db.Text)
    start_times = db.Column(db.Text)
    target_months = db.Column(db.Text)
    description = db.Column(db.Text)
    buffer = db.Column(db.Integer)
    reload_time = db.Column(db.Integer)
    no_of_reloads = db.Column(db.Integer)
    otp = db.Column(db.String(8), nullable=True)
    otp_exp = db.Column(db.DateTime(timezone=True), nullable=True)
    cookies = db.Column(db.Text) #Used to store static cookies between sessions


    def __repr__(self):
        return self.username
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}