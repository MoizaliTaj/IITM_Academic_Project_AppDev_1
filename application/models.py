from .database import db


class Deck_Data(db.Model):
    __tablename__ = 'deck_data'
    deck_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    deck_name = db.Column(db.String)
    deck_master_name = db.Column(db.String)
    deck_answer = db.Column(db.String, nullable=False)
    deck_option_1 = db.Column(db.String, nullable=False)
    deck_option_2 = db.Column(db.String, nullable=False)
    deck_option_3 = db.Column(db.String, nullable=False)
    deck_option_4 = db.Column(db.String, nullable=False)
    deck_language = db.Column(db.String, nullable=False)
    deck_rating = db.Column(db.Integer)
    deck_rating_count = db.Column(db.Integer)


class Deck_Scores(db.Model):
    __tablename__ = 'deck_scores'
    field_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False)
    deck_name = db.Column(db.String, nullable=False)
    deck_master_name = db.Column(db.String, nullable=False)
    deck_id = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.String, nullable=False)
    start_time_perf = db.Column(db.Integer, nullable=False)
    end_time = db.Column(db.String, )
    end_time_perf = db.Column(db.Integer, )
    score = db.Column(db.Integer, )


class Users(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.String, nullable=False)

