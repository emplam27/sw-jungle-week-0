import os
from flask import Flask, render_template, request, jsonify, redirect, make_response
from flask_jwt_extended import *
from flask_wtf.csrf import CSRFProtect
from pymongo import MongoClient
import datetime
from bson.objectid import ObjectId

app = Flask(__name__)

# JWT 매니저 활성화
app.config.update(DEBUG=True, JWT_SECRET_KEY="thisissecertkey")
# 정보를 줄 수 있는 과정도 필요함 == 토큰에서 유저 정보를 받음

jwt = JWTManager(app)

# JWT 쿠키 저장
app.config['JWT_COOKIE_SECURE'] = False  # https를 통해서만 cookie가 갈 수 있는지 (production 에선 True)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'  # access cookie를 보관할 url (Frontend 기준)
app.config['JWT_REFRESH_COOKIE_PATH'] = '/'  # refresh cookie를 보관할 url (Frontend 기준)
# CSRF 토큰 역시 생성해서 쿠키에 저장할지
# (이 경우엔 프론트에서 접근해야하기 때문에 httponly가 아님)
app.config['JWT_COOKIE_CSRF_PROTECT'] = False

# csrf
csrf = CSRFProtect()
csrf.init_app(app)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

# Mongo DB
client = MongoClient('localhost', 27017)
db = client.w0projectdb



@app.route('/')
def home():
    return render_template('login.html')


# 회원가입
@app.route('/register', methods=['GET', 'POST'])
def register():
    # 회원가입 버튼을 누르면
    if request.method == 'GET':
        return render_template("register.html")

    # 회원가입완료 버튼을 누르면
    else:
        # 회원정보 생성
        username = request.form.get('username')
        email = request.form.get('email')
        ordinal = request.form.get('ordinal')
        userid = request.form.get('userid')
        password = request.form.get('password')
        re_password = request.form.get('re_password')

        userinfo = {'user_id': userid, 'user_name': username, 'user_pwd': password, 'user_email': email,
                    'ordinal': ordinal}

        if not (userid and username and password and re_password):
            return "모두 입력해주세요"
        elif password != re_password:
            return "비밀번호를 확인해주세요"
        else:  # 모두 입력이 정상적으로 되었다면 밑에명령실행(DB에 입력됨)
            db.users.insert_one(userinfo)
            return jsonify({'result' : "success"})


# 로그인
@app.route('/user/login', methods=['POST'])
def login():
    user_id = request.form['user_id']
    user_pwd = request.form['user_pwd']

    ## *** find_one 시에 아무것도 없을 때의 데이터 형태 알아야함 ***
    user = db.users.find_one({'user_id': user_id}, {'user_pwd': user_pwd})
    if user is None:
        return jsonify({'login': False})

    access_token = create_access_token(identity=user_id, expires_delta=False)
    refresh_token = create_refresh_token(identity=user_id)

    resp = make_response(redirect('/article/known'))

    # 서버에 저장
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)

    return resp

# (완료)
# 실명 게시판 목록페이지 보기
@app.route('/article/known', methods=['GET'])
@jwt_required
def get_known_article():
    articles = list(db.articles.find({'article_is_secret': False}).sort('article_created_at', -1))
    return render_template('article_home.html', articles=articles)

# (완료)
# 익명 게시판 목록페이지 보기
@app.route('/article/unknown', methods=['GET'])
@jwt_required
def get_unknown_article():
    articles = list(db.articles.find({'article_is_secret': True}).sort('article_created_at', -1))
    return render_template('article_home.html', articles=articles)


# (완료)
# 실명게시판 글쓰기
@app.route('/article/known/post', methods=['GET', 'POST'])
@jwt_required
@csrf.exempt
def known_post_articles():
    if request.method == 'GET':
        return render_template('article_form.html', article_is_secret=False)
    else: 
        article_title = request.form['article_title']
        article_content = request.form['article_content']
        now = datetime.datetime.now()
        article_created_at = now.today()  # 시간
        article_modified_at = now.today()  # 시간
        article_view = 0
        article_like = 0
        article_is_secret = False
        article_user_id = get_jwt_identity()

        db.articles.insert_one(
            {'article_title': article_title, 'article_content': article_content, 'article_created_at': article_created_at,
            'article_modified_at': article_modified_at, 'article_view': article_view, 'article_like': article_like,
            'article_is_secret': article_is_secret,
            'user_id': article_user_id})

        return redirect('/article/known')

# (완료)
# 익명게시판 글쓰기
@app.route('/article/unknown/post', methods=['GET', 'POST'])
@jwt_required
@csrf.exempt
def unknonw_write_articles():
    if request.method == 'GET':
        return render_template('article_form.html', article_is_secret=True)

    else: 
        article_title = request.form['article_title']
        article_content = request.form['article_content']
        now = datetime.datetime.now()
        article_created_at = now.today()  # 시간
        article_modified_at = now.today()  # 시간
        article_view = 0
        article_like = 0
        article_is_secret = True
        article_user_id = get_jwt_identity()

        db.articles.insert_one(
            {'article_title': article_title, 'article_content': article_content, 'article_created_at': article_created_at,
            'article_modified_at': article_modified_at, 'article_view': article_view, 'article_like': article_like,
            'article_is_secret': article_is_secret,
            'user_id': article_user_id})

        return redirect('/article/unknown')


# (완료)
# 게시판 상세페이지 (익명 + 실명)
@app.route('/article/<article_id>', methods=['GET'])
@jwt_required
def read_articles(article_id):
    article = db.articles.find_one({'_id': ObjectId(article_id)})
    user_id = get_jwt_identity()
    comments = db.comments.find({'article_key': ObjectId(article_id)})
    return render_template('article_detail.html', article=article, user_id=user_id, comments=comments)


# (완료)
# 게시글 수정 (익명 + 실명)
@app.route('/article/<article_id>/modify', methods=['GET', 'POST'])
@jwt_required
def modify_pro(article_id):
    article = db.articles.find_one({'_id': ObjectId(article_id)})
    user_id = get_jwt_identity()

    if article.user_id != user_id:
        return redirect('/article/{}'.format(article_id))

    if request.method == 'GET':
        return render_template('article_form.html', article=article)
    
    else:
        article_title = request.form['article_title']
        article_content = request.form['article_content']
        now = datetime.datetime.now()
        article_modified_at = now.today()
        db.articles.update_one({'_id': ObjectId(article_id)}, {'$set': {'article_title': article_title,
                                                            'article_content': article_content,
                                                            'article_modified_at': article_modified_at}})

        return redirect('/article/{}'.format(article_id))


# (완료)
# 삭제
@app.route('/article/<article_id>/delete', methods=['POST'])
def delete_articles(article_id):
    article = db.articles.find_one({'_id': ObjectId(article_id)})
    user_id = get_jwt_identity()

    if article.user_id != user_id:
        return redirect('/article/{}'.format(article_id))
    
    db.articles.delete_one({'_id': ObjectId(article_id)})
    return redirect('/article/known')



if __name__ == '__main__':
    app.run('127.0.0.1', port=5000, debug=True)
