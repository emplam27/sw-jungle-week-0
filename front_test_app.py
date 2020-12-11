import os
from flask import Flask, render_template, request, jsonify, redirect, make_response
from flask_jwt_extended import *
from flask_wtf.csrf import CSRFProtect
from pymongo import MongoClient
import datetime
from bson.objectid import ObjectId
import json

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
# csrf = CSRFProtect()
# csrf.init_app(app)
# SECRET_KEY = os.urandom(32)
# app.config['SECRET_KEY'] = SECRET_KEY

# Mongo DB
client = MongoClient('localhost', 27017)
db = client.w0projectdb


@jwt_optional
def check():
    user_id = get_jwt_identity()
    jungle_id = list(map(lambda x: x['user_id'], db.users.find({})))
    # jungle_id = jungle_users[0]
    # 없으면 true
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
        formdata = {
            'username': username,
            'email': email,
            'ordinal': ordinal,
            'userid': userid,
        }

        # 회원가입 실패
        if not username:
            return render_template('register.html', result=True, msg='이름을 입력해주세요.', formdata=formdata)
        if not email:
            return render_template('register.html', result=True, msg='슬랙에 가입한 이메일을 입력해주세요.', formdata=formdata)
        if not userid:
            return render_template('register.html', result=True, msg='아이디를 입력해주세요.', formdata=formdata)
        if not password:
            return render_template('register.html', result=True, msg='비밀번호를 입력해주세요.', formdata=formdata)
        if not re_password:
            return render_template('register.html', result=True, msg='비밀번호 확인을 입력해주세요.', formdata=formdata)
        
        # 회원가입 성공
        user = db.students.find_one({'stu_name': username, 'stu_email' : email})
        if user is None:
            return render_template('register.html', result=True, msg='정글 교육생이 아닙니다. 확인해주세요.', formdata=formdata)
        elif password != re_password:
            return render_template('register.html', result=True, msg='비밀번호 확인이 일치하지 않습니다. 확인해주세요.', formdata=formdata)
        else:  # 모두 입력이 정상적으로 되었다면 밑에명령실행(DB에 입력됨)
            userinfo = {'user_id': userid, 'user_name': username, 'user_pwd': password, 'user_email': email,
                        'ordinal': ordinal}
            db.users.insert_one(userinfo)
            return render_template('register.html', result=True, msg='회원가입 되었습니다.')


@app.route('/register/check', methods=['GET'])
def check_id():
    user_id = request.form.get('userid')

    checking = db.students.find_one({'user_id':user_id})
    if checking is not None:
        return jsonify({'result' : "fail", 'msg' : 'already'})


# 로그인
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'GET':
        return render_template('login.html')

    else:
        user_id = request.form['user_id']
        user_pwd = request.form['user_pwd']
        # 로그인 실패
        if not user_id:
            return render_template('login.html', result=True, msg='아이디를 입력해주세요.')
        if not user_pwd:
            return render_template('login.html', result=True, msg='비밀번호를 입력해주세요.')
        user = db.users.find_one({'user_id': user_id}, {'user_pwd': user_pwd})
        if user is None:
            return render_template('login.html', result=True, msg='회원정보가 존재하지 않습니다. 다시 확인해주세요.')

        # 로그인 성공
        access_token = create_access_token(identity=user_id, expires_delta=False)
        refresh_token = create_refresh_token(identity=user_id)
        resp = make_response(render_template('login.html', result=True, msg='로그인 되었습니다.'))

        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)
        return resp


# 로그아웃
@app.route('/token/remove', methods=['POST'])
def logout():
    # resp = jsonify({'logout': True})
    resp = make_response(redirect('/'))
    unset_jwt_cookies(resp)
    return resp



# 실명 게시판 목록페이지 보기
@app.route('/article/known', methods=['GET'])
@jwt_required
def get_known_article():
    if check() is True:
        return redirect('/')

    articles = list(db.articles.find({'article_is_secret': False}).sort('article_created_at', -1))
    return render_template('article_home.html', articles=articles)


# 익명 게시판 목록페이지 보기
@app.route('/article/unknown', methods=['GET'])
@jwt_optional
def get_unknown_article():
    if check() is True:
        return redirect('/')
    articles = list(db.articles.find({'article_is_secret': True}).sort('article_created_at', -1))
    return render_template('article_home.html', articles=articles)


# 실명게시판 글쓰기
@app.route('/article/known/post', methods=['GET', 'POST'])
@jwt_optional
def known_post_articles():
    if check() is True:
        return redirect('/')

    if request.method == 'GET':
        return render_template('article_form.html', article_is_secret=False)
    
    else:
        now = datetime.datetime.now()
        now_text = now.strftime("%Y-%m-%d %H:%M:%S")
        article_title = request.form['article_title']
        article_content = request.form['article_content']
        now = datetime.datetime.now()
        article_created_at = now_text  # 시간
        article_modified_at = now_text  # 시간
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


# 익명게시판 글쓰기
@app.route('/article/unknown/post', methods=['GET', 'POST'])
@jwt_optional
def unknonw_write_articles():
    if check() is True:
        return redirect('/')

    if request.method == 'GET':
        return render_template('article_form.html', article_is_secret=True)

    else:
        now = datetime.datetime.now()
        now_text = now.strftime("%Y-%m-%d %H:%M:%S")
        article_title = request.form['article_title']
        article_content = request.form['article_content']
        now = datetime.datetime.now()
        article_created_at = now_text  # 시간
        article_modified_at = now_text  # 시간
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


# 게시글 상세페이지 (익명 + 실명)
@app.route('/article/<article_id>', methods=['GET'])
@jwt_optional
def article_detail(article_id):
    if check() is True:
        return redirect('/')

    article = db.articles.find_one({'_id': ObjectId(article_id)})
    user_id = get_jwt_identity()
    comments = db.comments.find({'article_key': ObjectId(article_id)})
    is_like = db.likes.find_one({'user_id' : user_id,'article_key' : article['_id']})
    # 조회 후 조회수 1 증가, 증가된 후의 값 return
    article = db.articles.find_one_and_update({'_id': ObjectId(article_id)},
                                              {"$inc" : {"article_view" : 1}},return_document=True)
    return render_template('article_detail.html', article=article, user_id=user_id, comments=comments, is_like=is_like)


# 게시글 수정 (익명 + 실명)
@app.route('/article/<article_id>/modify', methods=['GET', 'POST'])
@jwt_optional
def modify_pro(article_id):
    if check() is True:
        return redirect('/')

    article = db.articles.find_one({'_id': ObjectId(article_id)})
    user_id = get_jwt_identity()
    if article['user_id'] != user_id:
        return redirect('/article/{}'.format(article_id))
    article_is_secret = article['article_is_secret']

    if request.method == 'GET':
        return render_template('article_form.html', article=article, article_is_secret=article_is_secret)

    else:
        now = datetime.datetime.now()
        now_text = now.strftime("%Y-%m-%d %H:%M:%S")
        article_title = request.form['article_title']
        article_content = request.form['article_content']
        article_modified_at = now_text
        db.articles.update_one({'_id': ObjectId(article_id)}, {'$set': {'article_title': article_title,
                                                            'article_content': article_content,
                                                            'article_modified_at': article_modified_at}})
        return redirect('/article/{}'.format(article_id))


# 게시글 삭제
@app.route('/article/<article_id>/delete', methods=['POST'])
def delete_articles(article_id):
    if check() is True:
        return redirect('/')

    article = db.articles.find_one({'_id': ObjectId(article_id)})
    user_id = get_jwt_identity()
    if article['user_id'] != user_id:
        return redirect('/article/{}'.format(article_id))
    db.articles.delete_one({'_id': ObjectId(article_id)})
    return redirect('/article/known')


# 게시글 좋아요
@app.route('/article/<article_key>/like')
@jwt_optional
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


# 댓글 작성
@app.route('/article/<article_key>/comment', methods=["POST"])
@jwt_optional
def post_comment(article_key):
    if check() is True:
        return redirect('/')

    now = datetime.datetime.now()
    now_text = now.strftime("%Y-%m-%d %H:%M:%S")
    user_id = get_jwt_identity()
    article_key = ObjectId(article_key)
    comment_content = request.form['comment_content']
    comment_created_at = now_text  # 시간
    comment_modified_at = now_text  # 시간

    db.comments.insert_one({'article_key' : article_key, 'user_id' : user_id,
                            'comment_content' : comment_content, 'comment_created_at' : comment_created_at,
                            'comment_modified_at' : comment_modified_at})

    return redirect('/article/{}'.format(article_key))

# 댓글 수정
@app.route('/comment/<comment_key>/modify', methods=["POST"])
def modify_comment(comment_key):
    if check() is True:
        return redirect('/')

    comment_content = request.form['comment_content']
    comment = db.comments.find_one({'_id' : ObjectId(comment_key)})
    db.comments.update_one({'_id' : ObjectId(comment_key)},
                           {'$set' : {'comment_content' : comment_content}})
    article_key = comment['article_key']
    return redirect("/article/{}".format(article_key))


# 댓글 삭제
@app.route('/comment/<comment_key>/delete', methods=["POST"])
def delete_comment(comment_key):
    if check() is True:
        return redirect('/')

    comment = db.comments.find_one({'_id' : ObjectId(comment_key)})
    article_key = comment['article_key']
    db.comments.delete_one({'_id' : ObjectId(comment_key)})
    return redirect('/article/{}'.format(article_key))


if __name__ == '__main__':
    app.run('127.0.0.1', port=5000, debug=True)
