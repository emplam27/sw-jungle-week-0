from flask import Flask, render_template, make_response
from pymongo import MongoClient

app = Flask(__name__)
app._static_folder = './static'

client = MongoClient('localhost', 27017)
db = client.w0projectdb


@app.route('/')
def home():
    article = db.articles.find_one({'article_title': '제목1'})
    comments = db.comments.find({})
    return render_template('article_detail.html', article = article, comments = comments, user_id='test')


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
