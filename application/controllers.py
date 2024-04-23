from flask import request, render_template, current_app as app, session
from werkzeug.utils import redirect
from application.models import Deck_Data
from application.models import Deck_Scores
from application.models import Users
from application.database import db
from datetime import datetime
import time
import random
import hashlib

app.secret_key = b'_#asd""asd/lm;asd%'

def hasher(hash_string):
    signature = hashlib.sha256(hash_string.encode()).hexdigest()
    return signature

def logged_in():
    if 'username' in session:
        return True
    else:
        return False

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'GET':
        return render_template("login.html", title='Login Required')
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = hasher(request.form['password'])
        userinfo = Users.query.filter(Users.username.ilike(username)).first()
        if userinfo != None:
            if (userinfo.username.lower() == username) and (userinfo.password == password):
                session['username'] = username
                Deck_Scores.query.filter_by(username=request.form['username'], score=None).delete()
                db.session.commit()
                return redirect(request.referrer)
        return render_template("error.html", type="login",title="Error")


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(request.referrer)


@app.route("/")
def index():
    if logged_in():
        return render_template("index.html", title='Home Page')
    else:
        return login()


@app.route('/review',methods=["GET", "POST"])
def review_deck_selection():
    if logged_in():
        deckMasterName = request.args.get('deckname')
        field_id = request.args.get('field_id')
        if deckMasterName:
            all_deck_name = Deck_Data.query.filter_by(deck_master_name=deckMasterName).with_entities(Deck_Data.deck_name).distinct().all()
            deck_name_done = Deck_Scores.query.filter_by(username=session['username'],deck_master_name=deckMasterName).filter(Deck_Scores.score.isnot(None)).with_entities(Deck_Scores.deck_name).all()
            deck_name_not_done = []
            for i in all_deck_name:
                found = False
                for j in deck_name_done:
                    if i[0] == j[0]:
                        found = True
                        break
                if found==False:
                    deck_name_not_done.append(i[0])
            if not deck_name_not_done:
                question_deckname = deck_name_done[(random.randint(0, len(deck_name_done) - 1))][0]
            else:
                question_deckname = deck_name_not_done[(random.randint(0, len(deck_name_not_done) - 1))]
            dump = Deck_Data.query.filter_by(deck_name=question_deckname).first()
            deck_name = dump.deck_name
            deck_master_name = dump.deck_master_name
            rating = dump.deck_rating
            rating_count = dump.deck_rating_count
            deck_id = dump.deck_id
            start_time = datetime.now().strftime("%d/%m/%y %H:%M:%S")
            start_time_perf = time.perf_counter()
            score_details_partial_update = Deck_Scores(username=session['username'], deck_name=deck_name,deck_master_name=deck_master_name, deck_id=deck_id,start_time=start_time, start_time_perf=start_time_perf)
            db.session.add(score_details_partial_update)
            db.session.commit()
            field_id = Deck_Scores.query.filter_by(username=session['username'], deck_name=deck_name,start_time=start_time, ).first().field_id
            return render_template("review.html", user_name=session['username'], data=dump, fld_id=field_id,rating=rating, rating_count=rating_count, type="reviewquestion")
        elif field_id:
            if request.method == "POST":
                try:
                    answer = request.form["answer"]
                except:
                    deck_master_name = Deck_Scores.query.filter_by(field_id=field_id).first().deck_master_name
                    return render_template("error.html", deckname=deck_master_name, type="noanswer")
                deck_score_details = Deck_Scores.query.filter_by(field_id=field_id).first()
                deck_data_details = Deck_Data.query.filter_by(deck_name=deck_score_details.deck_name).first()
                if answer == deck_data_details.deck_answer:
                    # answer is correct
                    end_time = datetime.now().strftime("%d/%m/%y %H:%M:%S")
                    end_time_perf = time.perf_counter()
                    if (end_time_perf - deck_score_details.start_time_perf) >= 300:
                        score = 0
                    else:
                        score = round(10 - ((10 / 300) * (end_time_perf - deck_score_details.start_time_perf)), 2)
                    deck_score_details.end_time = end_time
                    deck_score_details.end_time_perf = end_time_perf
                    deck_score_details.score = score
                    db.session.commit()
                    return render_template("error.html", deck_id=deck_data_details.deck_id,message='Your answer ' + str(deck_data_details.deck_answer) + ' is the correct answer.',type="rating")
                else:
                    end_time = datetime.now().strftime("%d/%m/%y %H:%M:%S")
                    end_time_perf = time.perf_counter()
                    score = 0
                    deck_score_details.end_time = end_time
                    deck_score_details.end_time_perf = end_time_perf
                    deck_score_details.score = score
                    db.session.commit()
                    return render_template("error.html", deck_id=deck_data_details.deck_id,message='Incorrect Answer. Correct answer is ' + str(deck_data_details.deck_answer), type="rating")
        else:
            deck_names = Deck_Data.query.with_entities(Deck_Data.deck_master_name).distinct().order_by(Deck_Data.deck_master_name).all()
            return render_template("review.html", deck_name=deck_names, title="Review",type="reviewhome")
    else:
        return login()


@app.route('/dashboard')
def dashboard():
    if logged_in():
        type = request.args.get('type')
        if type == "user":
            dump = Deck_Scores.query.filter_by(username=session['username']).order_by(Deck_Scores.deck_master_name,Deck_Scores.deck_name).all()
            deck_score_list = []
            overall_score = 0
            overall_score_sum = 0
            overall_score_count = 0
            for i in dump:
                if i.score is not None:
                    deck_score_list.append(i)
                    overall_score_sum += i.score
                    overall_score_count += 1
            if overall_score_count != 0:
                overall_score = round(overall_score_sum / overall_score_count, 2)
            return render_template("dashboard.html", Overall_Score=overall_score,deck_scores=deck_score_list, title='User Dashboard', type="user")
        elif type == "deck":
            dump_cards = Deck_Data.query.order_by(Deck_Data.deck_master_name, Deck_Data.deck_name).all()
            dump_deck = Deck_Data.query.filter(Deck_Data.deck_rating.isnot('None')).all()
            deck_score = {}
            for i in dump_deck:
                try:
                    current_rating_total = deck_score[i.deck_master_name][0]
                    current_count = deck_score[i.deck_master_name][1]
                    new_rating_total = current_rating_total + (i.deck_rating * i.deck_rating_count)
                    new_count = current_count + i.deck_rating_count
                    new_rating = round(new_rating_total / new_count, 2)
                    deck_score[i.deck_master_name] = [new_rating_total, new_count, new_rating]
                except:
                    deck_score[i.deck_master_name] = [(i.deck_rating * i.deck_rating_count), i.deck_rating_count,
                                                      ((i.deck_rating * i.deck_rating_count) / i.deck_rating_count)]
            dump_deck_out = []
            for i in sorted(deck_score):
                dump_deck_out.append((i, deck_score[i][2]))
            return render_template("dashboard.html", title='Deck Dashboard', card_data=dump_cards,deck_data=dump_deck_out, type="deck")
    else:
        return login()

@app.route('/rating/<int:deck_id>', methods=["POST"])
def rating(deck_id):
    if logged_in():
        if request.method == "POST":
            rating = request.form["rating"]
            if rating == '':
                deck_master_name = Deck_Data.query.filter_by(deck_id=deck_id).first().deck_master_name
                return render_template("error.html", deckname =deck_master_name,type="ratingblank")
            else:
                deck_data_details = Deck_Data.query.filter_by(deck_id=deck_id).first()
                current_rating = deck_data_details.deck_rating
                current_rating_count = deck_data_details.deck_rating_count
                if current_rating != 'None':
                    new_rating = ((current_rating * current_rating_count) + int(rating)) / (current_rating_count + 1)
                    deck_data_details.deck_rating = new_rating
                    deck_data_details.deck_rating_count = current_rating_count + 1
                    db.session.commit()
                else:
                    new_rating = rating
                    new_count = 1
                    deck_data_details.deck_rating = new_rating
                    deck_data_details.deck_rating_count = new_count
                    db.session.commit()
                deck_master_name = Deck_Data.query.filter_by(deck_id=deck_id).first().deck_master_name
                return render_template("error.html",deckname=deck_master_name, type="ratingdone")
    else:
        return login()


@app.route('/deck_management', methods=["GET", "POST"])
def dec_management():
    if logged_in():
        if session['username'] == 'admin':
            type = request.args.get('type')
            if type == "":
                    dump = Deck_Data.query.order_by(Deck_Data.deck_master_name, Deck_Data.deck_name).all()
                    return render_template("dec_management.html", deck_data=dump, type="None")
            elif type == "create":
                if request.method == "GET":
                    return render_template("dec_management.html", type="create")
                if request.method == "POST":
                    deck_name = request.form["deck_name"]
                    deck_master_name = request.form["deck_master_name"]
                    deck_answer = request.form["deck_answer"]
                    deck_option_1 = request.form["deck_option_1"]
                    deck_option_2 = request.form["deck_option_2"]
                    deck_option_3 = request.form["deck_option_3"]
                    deck_option_4 = request.form["deck_option_4"]
                    deck_language = request.form["deck_language"]
                    if (deck_answer == deck_option_1) or (deck_answer == deck_option_2) or (
                            deck_answer == deck_option_3) or (deck_answer == deck_option_4):
                        try:
                            deckdata = Deck_Data(deck_name=deck_name, deck_master_name=deck_master_name,deck_answer=deck_answer, deck_option_1=deck_option_1,deck_option_2=deck_option_2, deck_option_3=deck_option_3,deck_option_4=deck_option_4, deck_language=deck_language,deck_rating='None', deck_rating_count='None')
                            db.session.add(deckdata)
                            db.session.commit()
                            return render_template("error.html", type="deckadd")
                        except:
                            return render_template("error.html", type="deckadddup")
                    else:
                        return render_template("error.html", type="deckaddans")
            elif type=="update":
                deck_id = request.args.get('deckid')
                if request.method == "GET":
                    dump = Deck_Data.query.filter_by(deck_id=deck_id).first()
                    return render_template("dec_management.html",deck=dump, type="update")
                if request.method == "POST":
                    print("I was called")
                    deck_name = request.form["deck_name"]
                    deck_master_name = request.form["deck_master_name"]
                    deck_answer = request.form["deck_answer"]
                    deck_option_1 = request.form["deck_option_1"]
                    deck_option_2 = request.form["deck_option_2"]
                    deck_option_3 = request.form["deck_option_3"]
                    deck_option_4 = request.form["deck_option_4"]
                    deck_language = request.form["deck_language"]
                    if (deck_answer == deck_option_1) or (deck_answer == deck_option_2) or (
                            deck_answer == deck_option_3) or (deck_answer == deck_option_4):
                        try:
                            deck_data_details = Deck_Data.query.filter_by(deck_id=deck_id).first()
                            deck_score_details = Deck_Scores.query.filter_by(deck_name=deck_data_details.deck_name).all()
                            for i in deck_score_details:
                                i.deck_name = deck_name
                                i.deck_master_name = deck_master_name
                            deck_data_details.deck_master_name = deck_master_name
                            deck_data_details.deck_name = deck_name
                            deck_data_details.deck_answer = deck_answer
                            deck_data_details.deck_option_1 = deck_option_1
                            deck_data_details.deck_option_2 = deck_option_2
                            deck_data_details.deck_option_3 = deck_option_3
                            deck_data_details.deck_option_4 = deck_option_4
                            deck_data_details.deck_language = deck_language
                            db.session.commit()
                            return render_template("error.html",type="deckupdate")
                        except:
                            return render_template("error.html",type="deckupdatedup",deckid=deck_id)
                    else:
                        return render_template("error.html",type="deckupdateans",deckid=deck_id,)
            elif type=="delete":
                deck_id = request.args.get('deckid')
                deck_name = Deck_Data.query.filter_by(deck_id=deck_id).first().deck_name
                Deck_Data.query.filter_by(deck_id=deck_id).delete()
                Deck_Scores.query.filter_by(deck_name=deck_name).delete()
                db.session.commit()
                return render_template("error.html",type="deckdelete")
        else:
            return render_template("error.html", type="unauthorised"), 401
    else:
        return login()



