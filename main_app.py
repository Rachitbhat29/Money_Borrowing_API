from flask import Flask, jsonify, request, make_response, g, session
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_caching import Cache
from flask_swagger_ui import get_swaggerui_blueprint
from datetime import datetime
from passlib.apps import custom_app_context as pwd_context
import uuid
import logging.handlers

# instantiate flask object
app = Flask(__name__)
CORS(app)
app.secret_key = "secret_key"

config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}

app.config.from_mapping(config)
cache = Cache(app)

# set app configs
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database2.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)

# create db instance
db = SQLAlchemy(app)

# instanctiate ma
ma = Marshmallow(app)

# create model
class TransactionList(db.Model):
    '''
    Store each trnsaction into Trnsaction_List table

    :transaction_id : unique id for each transaction
    :user_id = user_id
    :transaction_type : transaction type(Borrow/Lead)
    :transaction_amount : Amount ( Positive/Negative)
    :transaction_date : Transaction Date
    :transaction_status status for transaction (Paid or Unpaid)
    :transaction_with_userid : transaction with user id
    :reason : Reason
    '''
    transaction_id = db.Column(db.String(200), primary_key=True)
    user_id = db.Column(db.String(200),nullable=False)
    transaction_type = db.Column(db.Enum('B','L'),nullable=False)
    transaction_amount = db.Column(db.Float(), nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    transaction_status = db.Column(db.Enum('Paid','Unpaid'),nullable=False)
    transaction_with_userid = db.Column(db.String(200))
    reason = db.Column(db.String(200))

class Users(db.Model):
    '''
    Store each user details

    :id: Unique id for user
    :username : username
    :password: password saved with encryption
    "balance : balance
    '''

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200))
    password_hash = db.Column(db.String(500), nullable=False)
    balance = db.Column(db.Float(), nullable=False)

    def hash_password(self, password):
        ''' Method to hash the string password field'''
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        '''Method to verify the incoming passeord string with the hashed value'''
        return pwd_context.verify(password, self.password_hash)



# create db schema class
class UserSchema(ma.Schema):
    class Meta:
        user_model = Users

class TransactionListSchema(ma.Schema):
    class Meta:
        fields = ("transaction_id", "user_id", "transaction_type", "transaction_amount", "transaction_date"
                  , "transaction_status", "transaction_with_userid","reason")


# instantiate schema objects for Userlist and trnsactionlist
user_schema = UserSchema(many=True)
transactionlist_schema = TransactionListSchema(many=False)
transactionlists_schema = TransactionListSchema(many=True)


# error handeling
@app.errorhandler(400)
def handle_400_error(_error):
    """Return a http 400 error to client"""
    return make_response(jsonify({'error': 'Misunderstood'}), 400)


@app.errorhandler(401)
def handle_401_error(_error):
    """Return a http 401 error to client"""
    return make_response(jsonify({'error': 'Unauthorised'}), 401)


@app.errorhandler(404)
def handle_404_error(_error):
    """Return a http 404 error to client"""
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(500)
def handle_500_error(_error):
    """Return a http 500 error to client"""
    return make_response(jsonify({'error': 'Server error'}), 500)


@app.route("/login", methods=["POST"])
@cache.cached(timeout=50)
def login():
    '''Login end point for verifying user from db.

    :username : username for a user
    :password : password
    '''
    try:
        print(request.json)
        username = request.json.get('username')
        password = request.json.get('password')
        user = Users.query.filter_by(username=username).first()
        if not user or not user.verify_password(password):
            return jsonify({'Error': f'User:{username} does not exist'})
        session['user'] = user.id
        return jsonify({'Msg':'Login Successful'}), 200
    except Exception as e:
        print(e)
        return jsonify({"Error": "Invalid Request, please try again."})

# add a transaction
@app.route("/add_transaction", methods=["POST"])
@cache.cached(timeout=50)
def add_transaction():
    '''
    To add trnsaction for a user to db

    :user_id = user_id
    :transaction_type : transaction type(Borrow/Lead)
    :transaction_amount : Amount ( Positive/Negative)
    :transaction_status status for transaction (Paid or Unpaid)
    :transaction_with_userid : transaction with user id
    :reason : Reason
    '''
    try:
        id = str(uuid.uuid4())
        user_id = request.json['user_id']
        type = request.json['transaction_type']
        amount = request.json['transaction_amount']
        status = request.json['transaction_status']
        transaction_with = request.json['transaction_with']
        reason = request.json['reason']
        new_transaction = TransactionList(transaction_id=id, user_id=user_id,transaction_type=type,
                                          transaction_amount=amount,transaction_status=status,
                                          transaction_date=datetime.utcnow(),
                                          transaction_with_userid=transaction_with,reason=reason)

        db.session.add(new_transaction)
        db.session.commit()

        return transactionlist_schema.jsonify(new_transaction)
    except Exception as e:
        print(e)
        return jsonify({"Error": "Invalid Request, please try again."})


# Mark paid a specific transaction
@app.route("/mark_paid/<string:transaction_id>", methods=["PATCH"])
@cache.cached(timeout=50)
def update_mark_paid_flag(transaction_id):
    '''To update mark_paid column value for a specific transaction for a user

    :transaction_id: unique transaction_id

    '''
    try:
        transaction = TransactionList.query.get_or_404(transaction_id)
        if not transaction:
            return jsonify({"Error": "No Transaction found."}), 400

        transaction.transaction_status = 'Paid'
        db.session.commit()
        return transactionlist_schema.jsonify(transaction)
    except Exception as e:
        return jsonify({"Error": "Invalid Request, please try again."}) ,400

# get a specific user transactions
@app.route("/get_transactions/<string:user_id>", methods=["GET"])
@cache.cached(timeout=50)
def get_user_specific_transactions(user_id):
    '''
    Get all transactions details for a specific user.

    :user_id : unqiue id for user
    '''
    try:
        all_transactions = TransactionList.query.filter(TransactionList.user_id==str(user_id)).all()
        if not all_transactions:
            return jsonify({"Error": "No Transaction found."}), 400

        return jsonify(transactionlists_schema.dump(all_transactions))
    except Exception as e:
        return jsonify({"Error": "Invalid Request, please try again."}) ,400


# Generate Credit Score
@app.route('/credit_score/<string:user_id>', methods=['GET'])
@cache.cached(timeout=50)
def get_credit_score(user_id):
    '''
    Calculate and Generate Credit score for a user

    :user_id : Unique id for user
    '''

    try:
        # Calculating the % amount borrowed and % amount lend
        perc_borrowed , perc_lend = calculate_perc_amount_borrowed_and_lend(user_id)
        tmp_borrw_score , tmp_lend_score = 0,0
        for idx,i in enumerate(range(100,0,-10)):
            if abs(i - perc_borrowed) <= 9.9:
                tmp_borrw_score = 100*(idx+1)
            if abs(i - perc_lend) <=9.9:
                tmp_lend_score = 2000 - (idx*100)

        total_score = tmp_borrw_score+tmp_lend_score
        return jsonify({'credit_score':total_score})
    except Exception as e:
        return jsonify({"Error": "Invalid Request, please try again."})


def calculate_perc_amount_borrowed_and_lend(user_id):
    '''
    Calculatie the % amount borrowed and % amount lend
    '''

    result = db.session.execute("select sum(CASE WHEN transaction_type='B' THEN transaction_amount END) B_cnt, "
                                "sum(CASE WHEN transaction_type='L' THEN transaction_amount END) L_cnt from "
                                "transaction_list where user_id = :val", {'val': user_id})
    if not result:
        return 0,0

    from collections import namedtuple

    Record = namedtuple('Record', result.keys())
    record = Record(*result.fetchall()[0])
    total_cnt = abs(record.B_cnt) + abs(record.L_cnt)
    perc_amount_borrowed = abs(round((record.B_cnt/total_cnt)* 100,1))
    perc_amount_lend = abs(round((record.L_cnt / total_cnt) * 100,1))

    return perc_amount_borrowed, perc_amount_lend



# def insert_row_in_user():
# '''Method to insert data in user table'''
#     try:
#         newToner = Users(id=1,
#                      username='rachit',
#                      password_hash='$6$rounds=656000$ilYk4oOUpoZB3iuZ$RrsDXEd18VCigiXqN1jlZmjwVsytrWZ/09FH1WLwO7xX7hwCbO.j8CsLYeMCSqEFPf6Cdz5VMmPAOeNreHFbO0',
#                      balance=0)
#
#         db.session.add(newToner)
#         db.session.commit()
#     except Exception as e:
#         print(e)

if __name__ == "__main__":
    # db.drop_all()
    # db.create_all()
    # db.session.commit()

    # Logging handlers
    handler = logging.handlers.RotatingFileHandler('app.log', maxBytes=12000, backupCount=5)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    handler.setFormatter(formatter)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    app.logger.addHandler(handler)
    app.run(debug=True)
