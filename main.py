from flask import Flask, render_template
from flask_socketio import SocketIO

from nltk.corpus import reuters
from nltk import bigrams, trigrams

from collections import Counter, defaultdict

import re
import pandas as pd
import numpy as np
import json

# Tugas: Buat klasifikasi untuk review anime negatif dan positif
loc = "E:/Genta/Nitip kakak/NLP/cbchatflask/"
df = pd.read_csv(loc + "dataset_rekomendasi_anime_dan_review.txt", sep="delimiter", header=None, engine="python")

data = []
for d in df.values:
    data.append(d[0].lower().split())

kamus = []
for sentence in data:
    for word in sentence:
        x = True
        
        if kamus:
            for content in kamus:
                if content == word:
                    x = False
                    break

        if x:
            kamus.append(word)

model = defaultdict(lambda: defaultdict(lambda: 0))
for sentence in data:
    for w1, w2 in bigrams(sentence,pad_right=True,pad_left=True):
        model[w1][w2] += 1

for w1 in model:
    total_count = float(sum(model[w1].values()))

    for w2 in model[w1]:
        model[w1][w2] /= total_count

# Using Model
# print(model[None]["min"])

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)

@app.route('/')
def sessions():
    return render_template('session.html')

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)

    if json['data']:
         json = {
              'message' : 'Halo, apa yang ingin anda bicarakan?'
         }
    else:
         temp = botReg(json['message'])
         if len(temp) == 0:
              temp = botLev(json['message'])

         json = {
              'message' : botChoice(temp)
         }

    socketio.emit('bot response', json, callback=messageReceived)

@socketio.on('typing')
def handle_typing(json):
     print(str(json))

     temp = json['data'].split()
     data = getProbability(temp[len(temp)-1])
     json = {
          'suggestion' : data
     }

     socketio.emit('get suggestion',json, callback=messageReceived)

def levenhstein(base,comp):
    if base == comp: return 0
    elif len(base) == 0: return len(comp)
    elif len(comp) == 0: return len(base)
    v0 = [None] * (len(comp) + 1)
    v1 = [None] * (len(comp) + 1)
    for i in range(len(v0)):
        v0[i] = i
    for i in range(len(base)):
        v1[0] = i + 1
        for j in range(len(comp)):
            cost = 0 if base[i] == comp[j] else 1
            v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
        for j in range(len(v0)):
            v0[j] = v1[j]
            
    return v1[len(comp)]

def botLev(string):
    words = string.split()

    patterns = [
        ['action','sliceoflife','horror','romance'],    # 0 = genre
        ['rekomendasi','saran']                         # 1 = minta rekomendasi
    ]

    result = []
    for word in words:
        min = 9999
        id = -1
        jd = -1

        for index, pattern in enumerate(patterns):
            for jndex, item in enumerate(pattern):
                lev = levenhstein(word,item)

                if(lev < min):
                    min = lev
                    id = index
                    jd = jndex
        
        if id != -1 and jd != -1:
            result.append([id,jd])
    
    return result

def botReg(string):
    patterns = [
        ['action','sliceoflife','horror','romance'],    # 0 = genre
        ['rekomen(dasi)?|saran']                        # 1 = minta rekomendasi
    ]
    
    result = []

    for index, pattern in enumerate(patterns):
        for jndex, item in enumerate(pattern):
            temp = re.findall(item,string,re.IGNORECASE)
            if temp:
                result.append([index,jndex])

    return result

def botDb(lists):
    database = [
        [   # 0 = Genre
            'Action',
            'Slice of Life',
            'Horror',
            'Romance'
        ],
        [   # 1 = Action
        'Code Geass',
        'Psycho Pass',
        'Land of Lustrous',
        'Attack on Titan',
        'Fate/Zero'
        ],
        [   # 2 = Slice of Life
        'Daily Life of Highschool Boys',
        'Nichijou',
        'Laid Back Camp',
        'Flying Witch',
        'Non Non Biyori'
        ],
        [   # 3 = Horror
        'Shiki',
        'Another',
        'Junji Ito Collection',
        'Yamishibai',
        'Gakkou Gurashi'
        ],
        [   # 4 = Romance
        'Your Lie in April',
        'Clannad',
        'Your Name',
        'Shape of Voice',
        'Nisekoi'
        ]
    ]

    if lists[0][0] == 1:
        return database[0]
    else:
        return database[lists[0][1]+1]

def botChoice(lists):
    string = ""
    db = botDb(lists)
    
    if lists[0][0] == 1:
        string = "Boleh! Mau genre apa? Di database kami ada genre "
        for i, data in enumerate(db):
            if i < len(db) - 1:
                string = string + data + ", "
            else:
                string = string + "dan " + data
    else:
        string = "Rekomendasi kami ada "

        for i, data in enumerate(db):
            if i < len(db) - 1:
                string = string + data + ", "
            else:
                string = string + "dan " + data

    return string

def getZero(e):
     return e[0]

def getProbability(word):
     probability = []
     for content in kamus:
          temp = model[word][content]
          if temp > 0:
               probability.append([temp,content])

     probability.sort(reverse=True,key=getZero)

     for i,p in enumerate(probability):
          probability[i] = p[1]

     return probability

if __name__ == '__main__':
    socketio.run(app, debug=True)