# -*- coding: utf-8 -*-
"""
Created on Sun Jan 31 19:37:13 2021

@author: norok
"""
from flask import Flask, request, abort
import os
import MySQLdb
import random

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

# データベースに接続
connection = MySQLdb.connect(
    host='<データーベースのホスト名>',
    user='<データーベースのユーザ名>',
    passwd='<データーベースのパスワード>',
    db='<データベース名>')
cursor = connection.cursor()

# 正解判定
def check_quiz(text, keywords_correct):
    corrects_num = len(keywords_correct)
    check = 0
    for k in keywords_correct:
        if k in text:
            check += 1
    if check == len(keywords_correct):
        return True
    else:
        return False


#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = "<作成したチャネルのアクセストークンを入力>"
YOUR_CHANNEL_SECRET = "<作成したチャネルのChannel secretを入力>"

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/")
def hello_world():
#    res = ','.join(terms)
    return 'hello world!'

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = str(event.message.text)
    if message == 'クイズ':
        # 問題の取得
        cursor.execute("SELECT term FROM quiz")
        rows = cursor.fetchall()
        terms = []
        for row in rows:
            terms = terms + [row[0]]

        idx = random.randint(0,len(terms))
        q = terms[idx]
        res = q + ' とは何でしょう？'
        cursor.execute("UPDATE cur_quiz SET term= '{}' WHERE _id=0".format(q))
        connection.commit()
        connection.close()
    elif message != 'クイズ':
        # 出題した問題を取得
        cursor.execute("SELECT term FROM cur_quiz WHERE _id=0")
        current_quiz = cursor.fetchone()[0]
        if cursor.execute("SELECT term FROM quiz WHERE term='{}'".format(current_quiz)):
            ans_flag = True
            cursor.execute("SELECT keywords FROM quiz WHERE term='{}'".format(current_quiz))
            keywords_correct = cursor.fetchone()[0].split(',')
        else:
            ans_flag = False
        
        if ans_flag:
            if check_quiz(message, keywords_correct):
                res='正解!'
                connection.commit()
                connection.close()
            else:
                cursor.execute("SELECT `desc` FROM quiz WHERE term='{}'".format(current_quiz))
                desc = cursor.fetchone()[0]
                res = '残念。正解は、' + desc + 'です。'
                connection.commit()
                connection.close()
        else:
            res = 'エラー！「クイズ」と入力してください'
            connection.commit()
            connection.close()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=res))

if __name__ == "__main__":
#    app.run()
#    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=8080)