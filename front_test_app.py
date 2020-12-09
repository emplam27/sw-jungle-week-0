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


@jwt_optional
def check():
    user_id = get_jwt_identity()
    jungle_id = list(map(lambda x: x['user_id'], db.users.find({})))
    print(jungle_id)
    # jungle_id = jungle_users[0]
    if ((user_id not in jungle_id) or (user_id is None)):
        return True


@app.route('/')
@jwt_optional
def home():
    if get_jwt_identity():
        return redirect('/article/known')
    else:
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

        user = db.students.find_one({'user_name': username, 'user_email' : email})

        if user is None:
            return jsonify({'result' : 'fail' , 'msg' : 'student error'})
        elif not (userid and username and password and re_password):
            return jsonify({'result' : 'fail' , 'msg' : 'fill error'})
        elif password != re_password:
            return jsonify({'result' : 'fail','msg' : "pw error"})
        else:  # 모두 입력이 정상적으로 되었다면 밑에명령실행(DB에 입력됨)
            userinfo = {'user_id': userid, 'user_name': username, 'user_pwd': password, 'user_email': email,
                        'ordinal': ordinal}
            db.users.insert_one(userinfo)
            return jsonify({'result' : "success"})

@app.route('/register/check', methods=['GET'])
def check_id():
    user_id = request.form.get('userid')

    checking = db.students.find_one({'user_id':user_id})
    if checking is not None:
        return jsonify({'result' : "fail", 'msg' : 'already'})


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

    print(access_token)
    print(refresh_token)

    return resp


# (완료)
# 실명 게시판 목록페이지 보기
@app.route('/article/known', methods=['GET'])
@jwt_required
def get_known_article():
    if check() is True:
        return redirect('/')
    articles = list(db.articles.find({'article_is_secret': False}).sort('article_created_at', -1))
    return render_template('article_home.html', articles=articles)

# (완료)
# 익명 게시판 목록페이지 보기
@app.route('/article/unknown', methods=['GET'])
@jwt_required
def get_unknown_article():
    if check() is True:
        return redirect('/')
    articles = list(db.articles.find({'article_is_secret': True}).sort('article_created_at', -1))
    return render_template('article_home.html', articles=articles)


# (완료)
# 실명게시판 글쓰기
@app.route('/article/known/post', methods=['GET', 'POST'])
@jwt_required
@csrf.exempt
def known_post_articles():
    if check() is True:
        return redirect('/')

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
    if check() is True:
        return redirect('/')

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
    if check() is True:
        return redirect('/')
    article = db.articles.find_one({'_id': ObjectId(article_id)})
    user_id = get_jwt_identity()
    comments = db.comments.find({'article_key': ObjectId(article_id)})
    is_like = db.likes.find_one({'user_id' : user_id,'article_key' : article['_id']})
    return render_template('article_detail.html', article=article, user_id=user_id, comments=comments, is_like=is_like)


# (완료)
# 게시글 수정 (익명 + 실명)
@app.route('/article/<article_id>/modify', methods=['GET', 'POST'])
@jwt_required
def modify_pro(article_id):
    if check() is True:
        return redirect('/')

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
    if check() is True:
        return redirect('/')

    article = db.articles.find_one({'_id': ObjectId(article_id)})
    user_id = get_jwt_identity()
    if article.user_id != user_id:
        return redirect('/article/{}'.format(article_id))
    db.articles.delete_one({'_id': ObjectId(article_id)})
    return redirect('/article/known')


# 게시판 좋아요 기능 ## 주소
@app.route('/article/<article_key>/like')
@jwt_required
def like_articles(article_key):
    if check() is True:
        return redirect('/')

    article = db.articles.find_one({'_id': ObjectId(article_key)})
    user_id = get_jwt_identity()

    like_info = {'user_id' : user_id,'article_key' : article['_id']}
    is_like = db.likes.find_one(like_info)
    if is_like is None:
        db.likes.insert_one(like_info)
        db.articles.update_one({'_id' : ObjectId(article_key)},{'$inc' : {'article_like' : 1}})
        return jsonify({"result": "like"})
    else :
        db.likes.delete_one(like_info)
        db.articles.update_one({'_id': ObjectId(article_key)}, {'$inc': {'article_like': -1}})
        return jsonify({"result" : "non-like"})


# 댓글 완료 버튼
@app.route('/article/<article_key>/comment', methods=["POST"])
@jwt_required
def post_comment(article_key):
    if check() is True:
        return redirect('/')

    user_id = get_jwt_identity()
    article_key = ObjectId(article_key)
    comment_content = request.form['comment_content']
    now = datetime.datetime.now()
    comment_created_at = now.today()  # 시간
    comment_modified_at = now.today()  # 시간

    db.comments.insert_one({'article_key' : article_key, 'user_id' : user_id,
                            'comment_content' : comment_content, 'comment_created_at' : comment_created_at,
                            'comment_modified_at' : comment_modified_at})

    return redirect('/article/{}'.format(article_key))

# 댓글 수정버튼 누르면


# 댓글 수정완료 버튼
# 그 놈 클릭 시 어떻게 댓글 지칭?
@app.route('/article/<comment_key>', methods=["PUT"])
def modify_comment(comment_key):
    if check() is True:
        return redirect('/')

    comment_content = request.form['comment_content']
    comment = db.comments.find_one({'_id' : ObjectId(comment_key)})
    db.comments.update_one({'_id' : ObjectId(comment_key)},
                           {'$set' : {'comment_content' : comment_content}})
    article_key = comment['article_key']
    # return redirect("/article/{}".format(article_key))
    return redirect(url_for("read_articles", article_key = article_key))

    # return redirect('/article/{}'.format(article_key), comment = comment)

# 댓글 삭제 버튼
@app.route('/article/<comment_key>', methods=["DELETE"])
def delete_comment(comment_key):
    if check() is True:
        return redirect('/')

    comment = db.comments.find_one({'_id' : ObjectId(comment_key)})
    article_key = comment['article_key']
    db.comments.delete_one({'_id' : ObjectId(comment_key)})
    return redirect('/article/{}'.format(article_key))


if __name__ == '__main__':
    app.run('127.0.0.1', port=5000, debug=True)
