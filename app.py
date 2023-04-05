from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = 'kraftonjungle'

# MongoDB 연결
client = MongoClient('localhost', 27017)
db = client.test02


@app.route('/')
def login():
   return render_template('login.html')

# @app.route('/api/login', methods=['POST'])
# def check_login():
#     # POST 요청에서 데이터 추출
#     user_id = request.form['id']
#     password = request.form['password']

#     # mongoDB 에서 데이터 조회
#     user = db.user.find_one({'id': user_id, 'password': password})

#     # 로그인 정보가 일치하면 home 으로 redirect
#     if user:
#         flash('로그인 성공!')
#         return redirect(url_for('home'))
#     # 일치하지 않으면 다시 로그인 페이지로 redirect
#     else:
#         return redirect(url_for('login'))

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
        return jsonify({'result': 'success', 'redirect': '/home'})
    # 일치하지 않으면 다시 로그인 페이지로 redirect
    else:
        return jsonify({'result': 'fail'})
    

@app.route('/signup')
def signup():
   return render_template('signup.html')

@app.route('/api/signup', methods=['POST'])
def post_signup():
    # 1. 클라이언트로부터 데이터를 받기
    id_receive = request.form['id_give']  # 클라이언트로부터 url을 받는 부분
    password_receive = request.form['password_give']  # 클라이언트로부터 comment를 받는 부분
    check_password_receive = request.form['check_password_give']
    nickname_receive = request.form['nickname_give']
    name_receive = request.form['name_give']

    users={'id':id_receive, 'password': password_receive, 'check_password':check_password_receive, 'nickname':nickname_receive,'name':name_receive}

    # 3. mongoDB에 데이터를 넣기
    db.user.insert_one(users)

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
def home():
   return render_template('home.html')

@app.route('/mypage')
def mypage():
    # 세션에서 user_id와 user_nickname 가져오기
    user_id = session.get('user_id')
    user_nickname = session.get('user_nickname')
    
    # 로그인되어 있지 않으면 로그인 페이지로 redirect
    if not user_id:
        return redirect(url_for('login'))
    
    # 현재 로그인한 사용자가 작성한 글만 조회
    articles = db.article.find({'user_id': user_id})
    
    return render_template('mypage.html', user_id=user_id, user_nickname=user_nickname, articles=articles)




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


#





if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)