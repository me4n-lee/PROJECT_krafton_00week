from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, Response
from pymongo import MongoClient
from bson import ObjectId
from flask_jwt_extended import  decode_token, JWTManager, jwt_required, get_jwt_identity, create_access_token
from functools import wraps
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'kraftonjungle'
app.config['JWT_SECRET_KEY'] = 'kraftonjungle'  # 실제로는 보안을 위해 별도의 파일에 저장해주세요.
jwt = JWTManager(app)

# MongoDB 연결
client = MongoClient('localhost', 27017)
db = client.zeroweek

#인증을 확인하고 인증되지 않은 사용자를 로그인 페이지로 리디렉션하는 데코레이터
# def jwt_required_redirect(fn):
#     @wraps(fn)
#     def wrapper(*args, **kwargs):
#         token = request.cookies.get('access_token')
#         if token is None:
#             return redirect(url_for('login'))
#         try:
#             jwt_required()(fn)(*args, **kwargs)
#         except:
#             return redirect(url_for('login'))
#         return fn(*args, **kwargs)
#     return wrapper
def jwt_required_redirect(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.cookies.get('access_token')
        if token is None:
            return redirect(url_for('login'))
        try:
            decode_token(token)
        except:
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


@app.route('/')
def login():
   return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def check_login():
    # POST 요청에서 데이터 추출
    user_id = request.form['id']
    password = request.form['password']

    # mongoDB 에서 데이터 조회
    user = db.user.find_one({'id': user_id, 'password': password})

    # 로그인 정보가 일치하면 home 으로 redirect
    if user:
        session['user_id'] = user_id
        session['user_nickname'] = user['nickname']
        flash('로그인 성공!')

        access_token = create_access_token(identity=user_id)
        return jsonify({'result': 'success', 'access_token': access_token, 'redirect': '/home'})
    # 일치하지 않으면 다시 로그인 페이지로 redirect
    else:
        return jsonify({'result': 'fail'})

    

@app.route('/signup')
def signup():
   return render_template('signup.html')

@app.route('/api/signup', methods=['POST'])
def post_signup():
    # 1. 클라이언트로부터 데이터를 받기
    id_receive = request.form['id_give']  
    password_receive = request.form['password_give'] 
    check_password_receive = request.form['check_password_give']
    nickname_receive = request.form['nickname_give']
    name_receive = request.form['name_give']
    email_receive = request.form['email_give']
    strength_receive = request.form['strength_give']
    weakness_receive = request.form['weakness_give']
    
    # 2. 받은 데이터를 딕셔너리 형태로 만들기
    user = {
        'id': id_receive, 
        'password': password_receive, 
        'check_password': check_password_receive, 
        'nickname': nickname_receive,
        'name': name_receive, 
        'email' : email_receive,
        'strength' : strength_receive,
        'weakness' : weakness_receive
    }

    # 3. mongoDB에 데이터를 넣기
    db.user.insert_one(user)

    return jsonify({'result': 'success'})

@app.route('/api/check_duplication', methods=['POST'])
def check_duplication():
    user_id = request.form['id']
    nickname = request.form['nickname']
    
    id_exist = bool(db.user.find_one({'id': user_id}))
    nickname_exist = bool(db.user.find_one({'nickname': nickname}))

    if id_exist:
        return jsonify({'result': 'fail', 'message': '이미 사용중인 아이디입니다.'})
    elif nickname_exist:
        return jsonify({'result': 'fail', 'message': '이미 사용중인 닉네임입니다.'})
    else:
        return jsonify({'result': 'success'})


@app.route('/home')
@jwt_required_redirect
def home():
   return render_template('home.html')

@app.route('/mypage')
@jwt_required_redirect
def mypage():
    # 세션에서 user_id와 user_nickname 가져오기
    user_id = session.get('user_id')
    user_nickname = session.get('user_nickname')
    
    # 로그인되어 있지 않으면 로그인 페이지로 redirect
    if not user_id:
        return redirect(url_for('login'))
    
    # 현재 로그인한 사용자가 작성한 글만 조회
    articles = db.article.find({'user_id': user_id})
    user_info = db.user.find({'id': user_id})
    
    return render_template('mypage.html', user_id=user_id, user_nickname=user_nickname, articles=articles, user_info=user_info)

# @app.route('/mypage')
# @jwt_required
# def mypage():
#     # 토큰에서 user_id 가져오기
#     user_id = get_jwt_identity()
    
#     # 사용자 정보 조회
#     user = db.user.find_one({'id': user_id})
#     user_nickname = user['nickname']
    
#     # 현재 로그인한 사용자가 작성한 글만 조회
#     articles = db.article.find({'user_id': user_id})
    
#     return render_template('mypage.html', user_id=user_id, user_nickname=user_nickname, articles=articles)


@app.route('/write')
def write():
    return render_template('write.html')

@app.route('/api/write', methods=['POST'])
def post_article():
    user_id = session.get('user_id')
    # 1. 클라이언트로부터 데이터를 받기
    url_receive = request.form['url_give']  # 클라이언트로부터 url을 받는 부분
    content_receive = request.form['content_give']  # 클라이언트로부터 comment를 받는 부분
    title_receive = request.form['title_give']
    category_receive = request.form['category_give']

    article={'category':category_receive, 'title': title_receive, 'url':url_receive, 'content':content_receive, 'user_id':user_id}

    # 3. mongoDB에 데이터를 넣기
    result = db.article.insert_one(article)
    new_id = str(result.inserted_id)
    db.article.update_one({'_id' : result.inserted_id}, {'$set':{'id':new_id}})
    return jsonify({'result': 'success'})


@app.route('/rewrite')
def rewrite():
    # URL의 쿼리스트링에서 id 값을 추출
    article_id = request.args.get('id')

    # 추출한 id 값으로 DB에서 해당 article을 조회
    article = db.article.find_one({'id': article_id})

    # rewrite.html 페이지를 렌더링하고, article 정보 전달
    return render_template('rewrite.html', article=article)




@app.route('/api/get_articles', methods=['GET'])
def get_articles():
    articles = list(db.article.find())
    for article in articles:
        article['_id'] = str(article['_id'])
    return jsonify({'articles': articles})

@app.route('/content')
def content():
    # URL의 쿼리스트링에서 id 값을 추출
    article_id = request.args.get('id')

    # 추출한 id 값으로 DB에서 해당 article을 조회
    article = db.article.find_one({'id': article_id})

    # content.html 페이지를 렌더링하고, article 정보 전달
    return render_template('content.html', article=article)

@app.route('/correction')
def correction():
    # URL의 쿼리스트링에서 id 값을 추출
    article_id = request.args.get('id')

    # 추출한 id 값으로 DB에서 해당 article을 조회
    article = db.article.find_one({'id': article_id})

    # content.html 페이지를 렌더링하고, article 정보 전달
    return render_template('correction.html', article=article)

#민혁

@app.route('/api/delete_article', methods=['DELETE'])
def delete_article():
    article_id = request.args.get('id')
    result = db.article.delete_one({'id': article_id})
    
    if result.deleted_count > 0:
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'fail'})

@app.route('/api/update_article', methods=['POST'])
def update_article():
    # URL의 쿼리스트링에서 id 값을 추출
    article_id = request.args.get('id')

    # 폼 데이터에서 게시글 정보를 가져옵니다.
    category = request.form.get('category')
    title = request.form.get('title')
    url = request.form.get('url')
    content = request.form.get('content')

    # 데이터베이스에 수정된 정보를 업데이트합니다.
    result = db.article.update_one({'id': article_id}, {'$set': {
        'category': category,
        'title': title,
        'url': url,
        'content': content
    }})

    # 업데이트가 완료되면 사용자를 원하는 페이지로 리다이렉트합니다.
    if result.modified_count > 0:
        return redirect(url_for('mypage'))
    else:
        return 'Fail to update article'

@app.route('/api/type', methods=['GET'])
def type():
    # POST 요청에서 데이터 추출
    type = request.args.get('type_give')
    category = list(db.article.find({'category' : type}, {'_id' : 0}))

    return jsonify({'result': 'success', 'category': category})

@app.route('/api/search', methods=['GET'])
def search():
    data = request.args.get('data_give')
    
    articles = db.article.find({'$or': [
        {'title': {'$regex': data}},
        {'content': {'$regex': data}},
        {'category': {'$regex': data}},
        {'id' : {'$regex':data}}
    ]})
    
    result = []
    for article in articles:
        result.append({
            'title': article['title'],
            'content': article['content'],
            'url': article['url'],
            'category': article['category'],
            'id': article['id']
        })
        
    return jsonify({'result': 'success', 'articles': result})

@app.route('/match')
@jwt_required_redirect
def match():
    return render_template('match.html')

#추천 사용자 목록 가져오기
@app.route('/api/match', methods=['GET'])
def matching():
    user_id = session.get('user_id')
    user = db.user.find_one({'id': user_id})
    weakness = user['weakness']
    m_list = list(db.user.find({'strength' : weakness}, {'_id' : 0}))


    return jsonify({'result': 'success', 'm_list': m_list})

#추천 사용자의 정보 보기
@app.route('/m_info')
def info():
    # URL의 쿼리스트링에서 id 값을 추출
    user_id = request.args.get('id')

    # 추출한 id 값으로 DB에서 해당 article을 조회
    articles = db.article.find({'user_id': user_id})
    u_info = db.user.find_one({'id': user_id})

    # m_info.html 페이지를 렌더링하고, 정보 전달
    return render_template('m_info.html', articles=articles, u_info=u_info)

@app.route('/api/m_accept', methods=['POST'])
def post_match():
    user_id = session.get('user_id')
    # 1. 클라이언트로부터 데이터를 받기
    title = request.form['title']  
    content = request.form['content'] 
    r_id = request.form['r_id']

    matching={'title':title, 'content': content, 'r_id':r_id, 'id':user_id}

    # 3. mongoDB에 데이터를 넣기
    result = db.matching.insert_one(matching)
    new_id = str(result.inserted_id)
    db.matching.update_one({'_id' : result.inserted_id}, {'$set' : {'new_id':new_id}})

    return jsonify({'result': 'success'})

@app.route('/api/m_receive', methods=['GET'])
def accept12():
    user_id = session.get('user_id')
    matches = list(db.matching.find({'r_id': user_id}, {'_id' : 0}))

    return jsonify({'result': 'success', 'matches': matches})

@app.route('/requesting')
def requesting():
    # URL의 쿼리스트링에서 id 값을 추출
    article_id = request.args.get('id')

    # 추출한 id 값으로 DB에서 해당 article을 조회
    article = db.matching.find_one({'new_id': article_id})

    # m_info.html 페이지를 렌더링하고, 정보 전달
    return render_template('m_accept.html', article=article)

@app.route('/api/email', methods=['POST'])
def sendEmail():
    real_id = session.get('user_id')
    user_id = request.form['user_id']
    article_id = request.form['article_id']
    matching_title = db.matching.find_one({'new_id':article_id})
    email_from = db.user.find_one({'id': real_id})
    email_to = db.user.find_one({'id': user_id})

    print(real_id)
    print(user_id)
    print(article_id)
    print(matching_title['title'])
    print(email_from['email'])
    print(email_to['email'])
    # 세션 생성
    s = smtplib.SMTP('smtp.gmail.com', 587)

    # TLS 보안 시작
    s.starttls()
    EMAIL = os.getenv('EMAIL')
    PASSWORD = os.getenv('PASSWORD')
    #로그인 인증
    s.login(EMAIL, PASSWORD)
    

    #보낼 메시지 설정
    msg = MIMEText(real_id + " " + "님이" + matching_title['title'] + " " + "에 대한 요청을 수락하셨습니다!" + email_from['email'] + " " +  "으로 자세한 내용을 보내주세요.")
    msg['Subject'] = matching_title['title'] + " " + '에 대한 매칭이 성사됐습니다!'
    msg['From'] = EMAIL
    msg['To'] = email_to['email']


    #메일보내기
    s.sendmail(EMAIL, email_to['email'], msg.as_string())

    #세션 종료
    s.quit()

    db.matching.delete_one({'new_id':article_id})

    return jsonify({'result': 'success'})

@app.route('/api/delete', methods=['POST'])
def deletematch():
    article_id = request.form['article_id']
    db.matching.delete_one({'new_id':article_id})

    return jsonify({'result': 'success'})

if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)