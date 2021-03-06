from flask import Flask, render_template, request, jsonify, redirect,make_response, url_for
from flask_jwt_extended import *
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

# 로그아웃 Blacklist 관련 토큰체크 설정
# 위에 써서 필요한가?(10번째 줄) app.config['JWT_SECRET_KEY'] = 'jungle-gym'  # Change this!
# app.config['JWT_BLACKLIST_ENABLED'] = True
# app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
# blacklist = set()

# @jwt.token_in_blacklist_loader
# def check_if_token_in_blacklist(decrypted_token):
#     jti = decrypted_token['jti']
#     return jti in blacklist

# Mongo DB
client = MongoClient('localhost', 27017)
db = client.dbname

# test - id 임시삽입
# db.users.insert_one({'user_id': 'test', 'user_pwd': 'test', 'user_name': '정글', 'user_email': '.com', 'user_ordinal': 1})
# db.articles.insert_one({'user_id' : 'test','article_title' : 'test_title','article_content' : 'test_content',
#                         'article_created_at' : datetime.datetime.now().today(), 'article_view' : 0,
#                         'article_like' :0, 'article_is_secret' : True})
# db.students.insert_one({'stu_name' : 'ㅂㅈㄷ', 'stu_email' : '@.com', 'stu_ordinal' : 1})
# db.comments.insert_one({'article_key' : 123, 'user_id' : 'test', 'comment_content' : 'test_comment',
#                         'comment_created_at' : datetime.datetime.now().today()})
# db.likes.insert_one({'user_id' : 'test' , 'article_key' : 123})
#



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
    user_pwd = request.form['user_pwd']
    user_id = request.form['user_id']


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

# Endpoint for revoking the current users access token
# @app.route('/logout', methods=['DELETE'])
# @jwt_required
# def logout():
#     jti = get_raw_jwt()['jti']
#     blacklist.add(jti)
#     # return jsonify({"msg": "Successfully logged out"}), 200
#     return redirect('/')

@app.route('/token/remove', methods=['POST'])
def logout():
    resp = make_response(redirect('/'))
    unset_jwt_cookies(jsonify({'logout': 'success'}))
    return resp, 200


# 목록페이지 보기
@app.route('/article/known', methods=['GET'])
def get_known_article():
    if check() is True:
        return redirect('/')
    articles = list(db.articles.find({}).sort('article_created_at', -1))
    return render_template('article_home.html', articles=articles)


@app.route('/article/unknown', methods=['GET'])
def get_unknown_article():
    if check() is True:
        return redirect('/')

    articles = list(db.articles.find({}))
    return render_template('article_home.html', articles=articles)

# 실명게시판 글쓰기버튼 작동
@app.route('/article/known/write')
def known_write_articles():
    if check() is True:
        return redirect('/')

    return render_template('modify.html', article_is_secret=False)


# 익명게시판 글쓰기버튼
@app.route('/article/unknown/write')
def unknonw_write_articles():
    if check() is True:
        return redirect('/')

    return render_template('modify.html', article_is_secret=True)


# 실명게시판 글쓰기 완료버튼 작동
@app.route('/article/known/post', methods=['POST'])
def known_post_articles():
    if check() is True:
        return redirect('/')

    article_title = request.form['title_input']
    article_content = request.form['content_input']
    now = datetime.datetime.now()
    article_created_at = now.today()  # 시간
    article_modified_at = now.today()  # 시간
    article_view = 0
    article_like = 0
    article_is_secret = False
    user_id = get_jwt_identity()

    db.articles.insert_one(
        {'article_title': article_title, 'article_content': article_content, 'article_created_at': article_created_at,
         'article_modified_at': article_modified_at, 'article_view': article_view, 'article_like': article_like,
         'article_is_secret': article_is_secret,
         'user_id': user_id})

    return redirect('/article/known')


# 게시판(익명 + 실명) 상세페이지 (GET ? POST ?)
@app.route('/article/<article_key>', methods=['GET'])
@jwt_required
def read_articles(article_key):
    if check() is True:
        return redirect('/')

    # 조회 후 조회수 1 증가, 증가된 후의 값 return
    article = db.articles.find_one_and_update({'_id': ObjectId(article_key)},
                                              {"$inc" : {"article_view" : 1}},return_document=True)
    user_id = get_jwt_identity()
    comment = list(db.comments.find({'article_key' : ObjectId(article_key)}))


    return render_template('article_detail.html', article=article, user_id=user_id, comment=comment)

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


# 수정 버튼을 누르면
@app.route('/article/<article_key>/modify', methods=['PUT'])
@jwt_required
def modify_articles(article_key):
    if check() is True:
        return redirect('/')

    article = db.articles.find_one({'_id': ObjectId(article_key)})
    return render_template('modify.html', article=article)


# 수정완료 버튼을 누르면
@app.route('/article/<article_key>/modify_pro')
@jwt_required
def modify_pro(article_key):
    if check() is True:
        return redirect('/')

    article_title = request.form['title_input']
    article_content = request.form['content_input']
    now = datetime.datetime.now()
    article_modified_at = now.today()
    # 조회수, 좋아요는 수정하지 않는다.

    db.articles.update_one({'_id': ObjectId(article_key)}, {'$set': {'article_title': article_title,
                                                          'article_content': article_content,
                                                          'article_modified_at': article_modified_at}})

    # return redirect('/article/<article_key>')
    return(redirect('/article/{}'.format(article_key)))


# 삭제
@app.route('/article/<article_key>/delete', methods=['DELETE'])
@jwt_required
def delete_articles(article_key):
    if check() is True:
        return redirect('/')

    db.articles.delete_one({'_id': ObjectId(article_key)})
    return redirect('/article/known')


# 익명게시판 글쓰기 완료시 작동
@app.route('/article/unknown', methods=['POST'])
def unknown_post_articles():
    if check() is True:
        return redirect('/')

    article_title = request.form['title_input']
    article_content = request.form['content_input']
    now = datetime.datetime.now()
    article_created_at = now.today()  # 시간
    article_modified_at = now.today()  # 시간
    article_view = 0
    article_like = 0
    article_is_secret = True
    user_id = get_jwt_identity()

    db.articles.insert_one(
        {'article_title': article_title, 'article_content': article_content, 'article_created_at': article_created_at,
         'article_modified_at': article_modified_at, 'article_view': article_view, 'article_like': article_like,
         'article_is_secret': article_is_secret,
         'user_id': user_id})

    return redirect('/article/unknown')


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
