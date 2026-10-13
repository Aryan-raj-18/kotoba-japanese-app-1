import json
from pathlib import Path
ROOT=Path(__file__).parent.resolve()
p=ROOT/'data'/'japan_explorer.json'
data=json.loads(p.read_text(encoding='utf-8'))

# Representative dialect/casual expressions. The note intentionally avoids
# implying that one expression represents every speaker in an entire region.
data['dialects']={
 'Hokkaido': {'jp':'なまら','reading':'なまら','en':'very / really','example':'なまら寒い！','example_reading':'なまら さむい！','example_en':'It is really cold!','note':'Representative Hokkaido casual speech.'},
 'Tohoku': {'jp':'んだ','reading':'んだ','en':'that’s right / yes','example':'んだ、そうだね。','example_reading':'んだ、そうだね。','example_en':'Yeah, that’s right.','note':'A representative Tohoku-style response; forms vary by prefecture.'},
 'Kanto': {'jp':'じゃん','reading':'じゃん','en':'isn’t it? / you know','example':'いいじゃん！','example_reading':'いいじゃん！','example_en':'That’s good, isn’t it!','note':'Casual speech strongly associated with the Kanto area historically, especially Kanagawa, and now widely used elsewhere too.'},
 'Chubu': {'jp':'でら','reading':'でら','en':'very / really','example':'でらおいしい。','example_reading':'でら おいしい。','example_en':'It is really delicious.','note':'A representative Nagoya/Aichi expression; Chubu contains many different dialects.'},
 'Kansai': {'jp':'ほんま','reading':'ほんま','en':'really / true','example':'ほんまにおいしい！','example_reading':'ほんまに おいしい！','example_en':'It’s really delicious!','note':'A well-known Kansai expression.'},
 'Chugoku': {'jp':'じゃけえ','reading':'じゃけえ','en':'because / that’s why','example':'雨じゃけえ、気をつけて。','example_reading':'あめ じゃけえ、きをつけて。','example_en':'Because it’s raining, be careful.','note':'A representative Hiroshima-area expression; wording varies across Chugoku.'},
 'Shikoku': {'jp':'〜けん','reading':'〜けん','en':'because / since','example':'暑いけん、水を飲もう。','example_reading':'あついけん、みずを のもう。','example_en':'Because it’s hot, let’s drink water.','note':'A representative western-Japan pattern heard in parts of Shikoku; local forms vary.'},
 'Kyushu': {'jp':'ばってん','reading':'ばってん','en':'but / however','example':'行きたいばってん、時間がない。','example_reading':'いきたい ばってん、じかんが ない。','example_en':'I want to go, but I don’t have time.','note':'A representative Kyushu expression, especially associated with western Kyushu.'},
 'Okinawa': {'jp':'めんそーれ','reading':'めんそーれ','en':'welcome','example':'沖縄へめんそーれ！','example_reading':'おきなわへ めんそーれ！','example_en':'Welcome to Okinawa!','note':'A famous Okinawan greeting from the Ryukyuan language tradition.'},
}

data['train_vocab']=[
 {'jp':'駅','reading':'えき','en':'station'},
 {'jp':'新幹線','reading':'しんかんせん','en':'bullet train'},
 {'jp':'切符','reading':'きっぷ','en':'ticket'},
 {'jp':'乗り場','reading':'のりば','en':'platform / boarding area'},
 {'jp':'出発','reading':'しゅっぱつ','en':'departure'},
 {'jp':'到着','reading':'とうちゃく','en':'arrival'},
]

data['train_routes']=[
 {'id':'tokaido','name':'Tokaido Shinkansen','jp':'東海道新幹線','icon':'🚄','description':'A learning journey along Japan’s classic Tokyo–Osaka corridor. Map pins use the nearest prefectural-capital stop represented in Kotoba.', 'stops':['tokyo','kanagawa','shizuoka','aichi','kyoto','osaka']},
 {'id':'tohoku','name':'Tohoku Shinkansen','jp':'東北新幹線','icon':'🚅','description':'Travel north from Tokyo through the Tohoku region while learning station Japanese.', 'stops':['tokyo','saitama','fukushima','miyagi','iwate','aomori']},
 {'id':'sanyo','name':'Sanyo Shinkansen','jp':'山陽新幹線','icon':'🚄','description':'Cross western Honshu from Osaka toward Fukuoka with major learning stops along the route.', 'stops':['osaka','hyogo','okayama','hiroshima','yamaguchi','fukuoka']},
 {'id':'kyushu','name':'Kyushu Shinkansen','jp':'九州新幹線','icon':'🚅','description':'A compact southbound route from Fukuoka through Kumamoto to Kagoshima.', 'stops':['fukuoka','kumamoto','kagoshima']},
]

data['seasons']={
 'spring': {'label':'Spring','jp':'春','icon':'🌸','tagline':'Cherry blossoms, gardens, and mild travel days.','recommended':['tokyo','chiba','yamanashi','kyoto','nara','okayama','fukuoka']},
 'summer': {'label':'Summer','jp':'夏','icon':'☀️','tagline':'Festivals, coastlines, green mountains, and cooler northern escapes.','recommended':['hokkaido','aomori','miyagi','nagano','kochi','kagoshima','okinawa']},
 'autumn': {'label':'Autumn','jp':'秋','icon':'🍁','tagline':'Colorful leaves, mountain scenery, and comfortable sightseeing.','recommended':['hokkaido','aomori','iwate','nagano','kyoto','nara','hiroshima']},
 'winter': {'label':'Winter','jp':'冬','icon':'❄️','tagline':'Snow country, winter food, illumination, and hot-spring travel.','recommended':['hokkaido','aomori','akita','yamagata','niigata','nagano','ishikawa']},
}

# Region-based season suggestions, with a few city-specific refinements.
region_seasons={
 'Hokkaido':['summer','winter'], 'Tohoku':['spring','autumn','winter'], 'Kanto':['spring','autumn'],
 'Chubu':['spring','autumn','winter'], 'Kansai':['spring','autumn'], 'Chugoku':['spring','autumn'],
 'Shikoku':['spring','summer'], 'Kyushu':['spring','summer'], 'Okinawa':['spring','summer']
}
overrides={'okinawa':['spring','summer'],'hokkaido':['summer','winter'],'kyoto':['spring','autumn'],'nara':['spring','autumn'],'niigata':['autumn','winter'],'nagano':['summer','autumn','winter']}

food_words=json.loads((ROOT/'data'/'japan_food_words.json').read_text(encoding='utf-8'))
food_by_jp={w['jp']:w for w in food_words}
data['food_words']=[]
for place in data['places']:
    place['best_seasons']=overrides.get(place['id'], region_seasons.get(place['region'],['spring','autumn']))
    food=(place.get('foods') or ['名物'])[0]
    local_food=food_by_jp[food]
    food_en=local_food['en'].split(' (')[0]
    data['food_words'].append(dict(local_food, place_id=place['id']))
    city=place['city_en']
    # Situation mode: same learning goal, localized context and food.
    place['situations']={
      'beginner': {
        'title':'Order a local specialty','scene':f'You are at a small restaurant in {city} and want to order {food_en}.',
        'prompt':'Which sentence is the simplest polite choice?',
        'correct':f'{food}をください。','reading':f'{local_food["reading"]}を ください。','en':f'Please give me {food_en}.',
        'options':[f'{food}をください。',f'{food}はどこですか。','駅はどこですか。','写真を撮ってください。']
      },
      'intermediate': {
        'title':'Ask for a recommendation','scene':f'You are choosing what to eat in {city}.',
        'prompt':'How do you ask the staff what they recommend?',
        'correct':'おすすめは何ですか。','reading':'おすすめは なんですか。','en':'What do you recommend?',
        'options':['おすすめは何ですか。','これは何時ですか。','駅まで何分ですか。','写真を見せてください。']
      },
      'advanced': {
        'title':'Ask about the local specialty','scene':f'You want a polite explanation of what people in {place["prefecture_en"]} are known for eating.',
        'prompt':'Which sentence is the most appropriate polite request?',
        'correct':'この地域の名物について教えていただけますか。','reading':'この ちいきの めいぶつについて おしえていただけますか。','en':'Could you tell me about this area’s local specialties?',
        'options':['この地域の名物について教えていただけますか。','名物を見ないことにしました。','この地域へ行ったことがありません。','名物しか食べてはいけません。']
      }
    }

data['version']=2
p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('updated',p)
