from flask import Flask, render_template, request, jsonify
from flask_jwt_extended import *
from pymongo import MongoClient

app = Flask(__name__)


# JWT 매니저 활성화
app.config.update(DEBUG = True, JWT_SECRET_KEY = "thisissecertkey" )
                  # 정보를 줄 수 있는 과정도 필요함 == 토큰에서 유저 정보를 받음

jwt = JWTManager(app)

# JWT 쿠키 저장
app.config['JWT_COOKIE_SECURE'] = False # https를 통해서만 cookie가 갈 수 있는지 (production 에선 True)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/' # access cookie를 보관할 url (Frontend 기준)
app.config['JWT_REFRESH_COOKIE_PATH'] = '/' # refresh cookie를 보관할 url (Frontend 기준)
# CSRF 토큰 역시 생성해서 쿠키에 저장할지
# (이 경우엔 프론트에서 접근해야하기 때문에 httponly가 아님)
app.config['JWT_COOKIE_CSRF_PROTECT'] = True


# Mongo DB
client = MongoClient('localhost', 27017)
db = client.dbname

# test - id
db.users.insert_one({'user_id' : 'test','user_pwd': 'test', 'user_name' : '정글','user_email': '.com','user_ordinal' : 1})


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/user/login', methods = ['POST'])
def login():
    user_id = request.form['id_input']
    user_pw = request.form['pw_input']
    print(user_id)
    print(user_pw)

    ## *** find_one 시에 아무것도 없을 때의 데이터 형태 알아야함 ***
    user = db.users.find_one( {'user_id' : user_id},{'user_pwd' : user_pw})
    if user is None:
        return jsonify({'login' : False})

    access_token = create_access_token(identity = user_id, expires_delta = False)
    refresh_token = create_refresh_token(identity = user_id)

    resp = jsonify({'login' : True})

    # 서버에 저장
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)

    print(access_token)
    print(refresh_token)
    return resp, 200


if __name__ == '__main__':
    app.run('127.0.0.1', port=5000, debug=True)