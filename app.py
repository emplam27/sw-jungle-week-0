from flask import Flask, render_template, request, jsonify, redirect
from flask_jwt_extended import *
from pymongo import MongoClient
import datetime

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
    user = db.articles.find_one( {'user_id' : user_id},{'user_pwd' : user_pw})
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

# 실명게시판 글쓰기버튼 작동
@app.route('/article/known/write')
def modify_articles():
    return render_template('modify.html', article_is_secret = False)

# 익명게시판 글쓰기버튼
@app.route('/article/unknown/write')
def modify_articles():
    return render_template('modify.html', article_is_secret = True)

# 실명게시판 글쓰기 완료버튼 작동
@app.route('/article/known/post', methods=['POST'])
def post_articles():
    article_title = request.form['title_input']
    article_content = request.form['content_input']
    now = datetime.datetime.now()
    article_created_at = now.today() # 시간
    article_modified_at = now.today()  # 시간
    article_view = 0
    article_like = 0
    article_is_secret = False
    article_user_id = get_jwt_identity()

    db.articles.insert_one({'article_title' : article_title, 'article_content' : article_content, 'article_created_at' : article_created_at,
                         'article_modified_at' : article_modified_at,'article_view' : article_view, 'article_like' : article_like, 'article_is_secret' :article_is_secret,
                         'article_user_id' : article_user_id})

    return redirect('/article/known')


# 실명게시판 상세페이지 (GET ? POST ?)
@app.route('/article/<article_id>', methods=['GET'])
def read_articles(article_id):
    article = db.articles.find_one({'_id' : article_id})
    user_id = get_jwt_identity()

    return render_template('read.html', article = article ,user_id = user_id)


# 수정 버튼을 누르면
@app.route('/article/<article_id>/modify', methods=['PUT'])
def modify_articles(article_id):
    article = db.articles.find_one({'_id' : article_id})
    return render_template('modify.html', article = article)

# 수정완료 버튼을 누르면
@app.route('/article/<article_id>/modify_pro')
def modify_pro(article_id):
    article_title = request.form['title_input']
    article_content = request.form['content_input']
    now = datetime.datetime.now()
    article_modified_at = now.today()


    db.articles.update_one({'_id': article_id }, {'$set':{'article_title' : article_title,
                                                          'article_content' : article_content,'article_modified_at' : article_modified_at}})

    return redirect('/article/known')


# 삭제
@app.route('/article/<article_id>/delete', methods=['DELETE'])
def delete_articles(article_id):
    db.articles.delete_one({'_id' : article_id})
    return  redirect('/article/known')



# 익명게시판 글쓰기 완료시 작동
@app.route('/article/unknown', methods=['POST'])
def post_articles():
    article_title = request.form['title_input']
    article_content = request.form['content_input']
    now = datetime.datetime.dnow()
    article_created_at = now.strftime('%m-%d %H:%M')  # 시간 : 월-일 시간-분
    article_view = 0
    article_like = 0
    article_is_secret = True
    article_user_id = get_jwt_identity()

    db.articles.insert_one({'article_title': article_title, 'article_content': article_content,
                         'article_created_at': article_created_at,
                         'article_view': article_view, 'article_like': article_like,
                         'article_is_secret': article_is_secret,
                         'article_user_id': article_user_id})


    # article_writer = "{}기 {}".format(user['user_ordinal'],user['user_name'])



@app.route('/article/known', methods=['GET'])
def get_articles():



if __name__ == '__main__':
    app.run('127.0.0.1', port=5000, debug=True)