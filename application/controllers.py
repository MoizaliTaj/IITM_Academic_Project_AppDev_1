from flask import request, make_response, render_template, current_app as app, session
from flask_restful import Resource, fields, marshal_with
from werkzeug.utils import redirect
from werkzeug.exceptions import HTTPException
from application.models import Deck_Data
from application.models import Deck_Scores
from application.models import Nav_Page_Info
from application.database import db
from datetime import datetime
import time
import random


class HTTPErrorHandler(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('', status_code)


output_fields_user = {
    "deck_master_name": fields.String,
    "deck_name": fields.String,
    "start_time": fields.String,
    "score": fields.Integer,
}


class User_Dashboard_API(Resource):
    @marshal_with(output_fields_user)
    def get(self, username):
        user = Deck_Scores.query.filter_by(username=username).order_by(Deck_Scores.deck_master_name,Deck_Scores.deck_name).all()
        if user:
            out = []
            for i in user:
                out.append(i)
            return out, 200
        else:
            raise HTTPErrorHandler(status_code=404)


output_fields_deck = {
    "deck_master_name": fields.String,
    "deck_name": fields.String,
    "deck_rating": fields.Integer,
    "deck_rating_count": fields.Integer,
}


class Deck_API(Resource):
    @marshal_with(output_fields_deck)
    def get(self, ):
        Deck = Deck_Data.query.filter(Deck_Data.deck_rating.isnot('None')).all()
        if Deck:
            out = []
            for i in Deck:
                out.append(i)
            return out, 200
        else:
            raise HTTPErrorHandler(status_code=404)


app.secret_key = b'_#asd""asd/lm;asd%'


# this is a function that is called by login as a way to provide login screen with a custom message
def login_custom(title, message, user):
    nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
    return render_template("login.html", title=title, message=message, user_name=user, nav_page=nav_page)


# this function is called when user tries to access a URL but he/she is not loged in. This function then provides option for user to login.
def login_not_loged_in():
    nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(
        Nav_Page_Info.page_num).all()
    return render_template("login.html", title='Login Required', message='You are not logged in currently. Kindly enter the details below and login', user_name='', nav_page=nav_page)


# login path function
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        Deck_Scores.query.filter_by(username=request.form['username'], score=None).delete()
        db.session.commit()
        return redirect("/")
    else:
        if 'username' in session:
            return login_custom('Already Logged in', 'User ' + str(session['username']) + ' is currently loged in. If you proceed to login below then current user will be loged out.', session['username'])
        else:
            return login_custom('Login', 'Kindly enter the details below.', '')


# logout path function
@app.route('/logout')
def logout():
    session.pop('username', None)
    nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(
            Nav_Page_Info.page_num).all()
    return render_template("logout.html", title='Logged Out', nav_page=nav_page)


# all the function below checks if user is logedin then it shows the required page, if not loged in it calls login_not_loged_in function


# this is the index page.
@app.route("/")
def index():
    if 'username' in session:
        nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(
            Nav_Page_Info.page_num).all()
        return render_template("index.html", title='Home Page', user_name=session['username'], nav_page=nav_page)
    else:
        return login_not_loged_in()


@app.route('/user_dashboard')
def dashboard():
    if 'username' in session:
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
        nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
        return render_template("dashboard.html", user_name=session['username'], Overall_Score=overall_score,deck_scores=deck_score_list, title='User Dashboard', nav_page=nav_page)
    else:
        return login_not_loged_in()


@app.route('/deck_dashboard')
def deck_dashboard():
    if 'username' in session:
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
        nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
        return render_template("dashboard_deck.html", user_name=session['username'], title='Deck Dashboard',nav_page=nav_page, card_data=dump_cards, deck_data=dump_deck_out)
    else:
        return login_not_loged_in()


@app.route('/review')
def review_deck_selection():
    if 'username' in session:
        dump_deck_name = Deck_Data.query.with_entities(Deck_Data.deck_master_name).distinct().order_by(
            Deck_Data.deck_master_name).all()
        nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
        return render_template("review_deck_selection.html", deck_name=dump_deck_name, title="Review",nav_page=nav_page, user_name=session['username'], )
    else:
        return login_not_loged_in()


@app.route('/review/<deck_master_name>')
def review(deck_master_name):
    if 'username' in session:
        deck_name_done_pre = Deck_Scores.query.filter_by(username=session['username'],deck_master_name=deck_master_name).filter(Deck_Scores.score.isnot(None)).with_entities(Deck_Scores.deck_name).all()
        deck_name_done = []
        for i in deck_name_done_pre:
            deck_name_done.append(i[0])
        all_deck_name_pre = Deck_Data.query.filter_by(deck_master_name=deck_master_name).with_entities(Deck_Data.deck_name).distinct().all()
        all_deck_name = []
        for i in all_deck_name_pre:
            all_deck_name.append(i[0])
        deck_name_not_done = []
        for i in all_deck_name:
            if i not in deck_name_done:
                deck_name_not_done.append(i)
        if not deck_name_not_done:
            question_deckname = deck_name_done[(random.randint(0, len(deck_name_done) - 1))]
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
        score_details_partial_update = Deck_Scores(username=session['username'], deck_name=deck_name,deck_master_name=deck_master_name,deck_id=deck_id,start_time=start_time, start_time_perf=start_time_perf)
        db.session.add(score_details_partial_update)
        db.session.commit()
        field_id = Deck_Scores.query.filter_by(username=session['username'], deck_name=deck_name,start_time=start_time, ).first().field_id
        nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
        return render_template("review_question.html", user_name=session['username'], data=dump, fld_id=field_id,rating=rating, rating_count=rating_count, nav_page=nav_page)
    else:
        return login_not_loged_in()


@app.route('/review/<int:field_id>', methods=["POST"])
def review_q(field_id):
    if 'username' in session:
        if request.method == "POST":
            try:
                answer = request.form["answer"]
            except:
                nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
                deck_master_name = Deck_Scores.query.filter_by(field_id=field_id).first().deck_master_name
                return render_template("submission.html", user_name=session['username'],message='No answer was selected. In 5 seconds redirecting back to a new card.',redirect='5', url_val='/review/' + str(deck_master_name), nav_page=nav_page)
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
                nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
                return render_template("rating.html", user_name=session['username'], deck_id=deck_data_details.deck_id,message='Your answer ' + str(deck_data_details.deck_answer) + ' is the correct answer.',nav_page=nav_page)
            else:
                end_time = datetime.now().strftime("%d/%m/%y %H:%M:%S")
                end_time_perf = time.perf_counter()
                score = 0
                deck_score_details.end_time = end_time
                deck_score_details.end_time_perf = end_time_perf
                deck_score_details.score = score
                db.session.commit()
                nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
                return render_template("rating.html", user_name=session['username'], deck_id=deck_data_details.deck_id,message='Incorrect Answer. Correct answer is ' + str(deck_data_details.deck_answer), nav_page=nav_page)
    else:
        return login_not_loged_in()


@app.route('/rating/<int:deck_id>', methods=["POST"])
def rating(deck_id):
    if 'username' in session:
        if request.method == "POST":
            rating = request.form["rating"]
            if rating == '':
                nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
                deck_master_name = Deck_Data.query.filter_by(deck_id=deck_id).first().deck_master_name
                return render_template("submission.html", user_name=session['username'],
                                       message='Redirecting to a new question',
                                       redirect='3', url_val='/review/' + str(deck_master_name), nav_page=nav_page)
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
                nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(
                    Nav_Page_Info.page_num).all()
                deck_master_name = Deck_Data.query.filter_by(deck_id=deck_id).first().deck_master_name
                return render_template("submission.html", user_name=session['username'],
                                       message='Thanks for providing the rating. Redirecting to a new question',
                                       redirect='3', url_val='/review/' + str(deck_master_name), nav_page=nav_page)
    else:
        return login_not_loged_in()


@app.route('/deck_management')
def dec_management():
    if 'username' in session:
        if session['username'] == 'Admin':
            dump = Deck_Data.query.order_by(Deck_Data.deck_master_name, Deck_Data.deck_name).all()
            nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
            return render_template("dec_management.html", user_name=session['username'], deck_data=dump,nav_page=nav_page)
        else:
            nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(
                Nav_Page_Info.page_num).all()
            return render_template("unauthorised.html", user_name=session['username'], nav_page=nav_page), 401
    else:
        return login_not_loged_in()


@app.route('/deck_management/create', methods=["GET", "POST"])
def dec_management_create():
    if 'username' in session:
        if session['username'] == 'Admin':
            if request.method == "GET":
                nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
                return render_template("dec_management_create.html", nav_page=nav_page, user_name=session['username'], )
            if request.method == "POST":
                deck_name = request.form["deck_name"]
                deck_master_name = request.form["deck_master_name"]
                deck_answer = request.form["deck_answer"]
                deck_option_1 = request.form["deck_option_1"]
                deck_option_2 = request.form["deck_option_2"]
                deck_option_3 = request.form["deck_option_3"]
                deck_option_4 = request.form["deck_option_4"]
                deck_language = request.form["deck_language"]
                if (deck_answer == deck_option_1) or (deck_answer == deck_option_2) or (deck_answer == deck_option_3) or (deck_answer == deck_option_4):
                    try:
                        deckdata = Deck_Data(deck_name=deck_name, deck_master_name=deck_master_name,deck_answer=deck_answer, deck_option_1=deck_option_1,deck_option_2=deck_option_2, deck_option_3=deck_option_3,deck_option_4=deck_option_4, deck_language=deck_language,deck_rating='None', deck_rating_count='None')
                        db.session.add(deckdata)
                        db.session.commit()
                        nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path,Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
                        return render_template("submission.html", user_name=session['username'],message='Deck added successfully. Redirecting to Deck Management',redirect='2',url_val='/deck_management', nav_page=nav_page)
                    except:
                        nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path,Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
                        return render_template("submission.html", user_name=session['username'],message='Duplicate Deck Name. Use another Deck Name. ',redirect='5',url_val='/deck_management', nav_page=nav_page)
                else:
                    nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path,Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
                    return render_template("submission.html", user_name=session['username'],message='Options do not match the answer. One of the options should contain the answer. This page will redirect in 5 seconds',redirect='5',url_val='/deck_management/create', nav_page=nav_page)
        else:
            nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path,Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
            return render_template("unauthorised.html", user_name=session['username'], nav_page=nav_page), 401
    else:
        return login_not_loged_in()


@app.route('/deck_management/<int:deck_id>/update', methods=["GET", "POST"])
def dec_management_update(deck_id):
    if 'username' in session:
        if session['username'] == 'Admin':
            if request.method == "GET":
                dump = Deck_Data.query.filter_by(deck_id=deck_id).first()
                nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path,Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
                return render_template("dec_management_update.html", user_name=session['username'], deck=dump,nav_page=nav_page)
            if request.method == "POST":
                deck_name = request.form["deck_name"]
                deck_master_name = request.form["deck_master_name"]
                deck_answer = request.form["deck_answer"]
                deck_option_1 = request.form["deck_option_1"]
                deck_option_2 = request.form["deck_option_2"]
                deck_option_3 = request.form["deck_option_3"]
                deck_option_4 = request.form["deck_option_4"]
                deck_language = request.form["deck_language"]
                if (deck_answer == deck_option_1) or (deck_answer == deck_option_2) or (deck_answer == deck_option_3) or (deck_answer == deck_option_4):
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
                        nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path,Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
                        return render_template("submission.html", user_name=session['username'],message='Deck updated successfully. Redirecting to Deck Management',redirect='2',url_val='/deck_management', nav_page=nav_page)
                    except:
                        nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path,Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
                        return render_template("submission.html", user_name=session['username'],message='Duplicate Deck Name. Use another Deck Name. ',redirect='5',url_val='/deck_management/' + str(deck_id) + '/update',nav_page=nav_page)
                else:
                    nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path,Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
                    return render_template("submission.html", user_name=session['username'],message='Options do not match the answer. One of the options should contain the answer. This page will redirect in 5 seconds',redirect='5',url_val='/deck_management/' + str(deck_id) + '/update', nav_page=nav_page)
        else:
            nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path,Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
            return render_template("unauthorised.html", user_name=session['username'], nav_page=nav_page), 401
    else:
        return login_not_loged_in()


@app.route('/deck_management/<int:deck_id>/delete', methods=["GET", "POST"])
def dec_management_delete(deck_id):
    if 'username' in session:
        if session['username'] == 'Admin':
            deck_name = Deck_Data.query.filter_by(deck_id=deck_id).first().deck_name
            Deck_Data.query.filter_by(deck_id=deck_id).delete()
            Deck_Scores.query.filter_by(deck_name=deck_name).delete()
            db.session.commit()
            nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
            return render_template("submission.html", user_name=session['username'],message='Deck deleted successfully. Redirecting to Deck Management',redirect='3',url_val='/deck_management', nav_page=nav_page)
        else:
            nav_page = Nav_Page_Info.query.with_entities(Nav_Page_Info.page_path, Nav_Page_Info.page_name).order_by(Nav_Page_Info.page_num).all()
            return render_template("unauthorised.html", user_name=session['username'], nav_page=nav_page), 401
    else:
        return login_not_loged_in()
