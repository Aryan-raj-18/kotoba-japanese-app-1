#!/usr/bin/env python3
"""Curated original real-life Kotoba Speaking & Shadowing sentence bank.

The supplied phrasebook inspired the broad idea of useful situations only. All
sentences, examples, details and English glosses here were independently written
for the app. No sentences are extracted from or mapped to book pages.
"""
import json, re, unicodedata
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent if (Path(__file__).resolve().parent/'app.py').exists() else Path('/mnt/data/kotoba_work/kotoba-1.0.0')
groups = []
def group(name, content):
    groups.append((name, content.strip()))

# Format: difficulty | Japanese target | segmented kana reading | English meaning.
# Segments are pronounced chunks so particles can be romanized correctly.
group('Morning routines', '''
E|今朝は六時に起きました。|けさ は ろくじ に おきました|I got up at six this morning.
E|まず水を一杯飲みます。|まず みず を いっぱい のみます|First, I drink a glass of water.
E|朝ご飯はまだです。|あさごはん は まだ です|I haven't had breakfast yet.
E|今日は早く出かけます。|きょう は はやく でかけます|I'm leaving early today.
E|毎朝公園を歩きます。|まいあさ こうえん を あるきます|I walk in the park every morning.
M|寝坊したので、急いで準備します。|ねぼう した ので いそいで じゅんび します|I overslept, so I'll get ready quickly.
M|コーヒーを入れてから仕事を始めます。|こーひー を いれて から しごと を はじめます|I'll make coffee before starting work.
M|今日はお弁当を持って行くつもりです。|きょう は おべんとう を もって いく つもり です|I'm planning to bring a packed lunch today.
M|出かける前に窓を閉めてください。|でかける まえ に まど を しめて ください|Please close the window before leaving.
M|朝は静かな音楽を聞くのが好きです。|あさ は しずかな おんがく を きく の が すき です|I like listening to calm music in the morning.
M|駅まで歩くと十五分ほどかかります。|えき まで あるく と じゅうごふん ほど かかります|It takes about fifteen minutes to walk to the station.
M|いつもより早く起きたので時間があります。|いつも より はやく おきた ので じかん が あります|I woke up earlier than usual, so I have time.
H|朝のうちに買い物を済ませておきたいです。|あさ の うち に かいもの を すませて おきたい です|I'd like to finish the shopping in the morning.
H|電車が混む前に家を出られるようにしています。|でんしゃ が こむ まえ に いえ を でられる ように しています|I try to leave home before the trains get crowded.
H|目覚ましをかけ忘れてしまい、約束に遅れそうです。|めざまし を かけわすれて しまい やくそく に おくれそう です|I forgot to set my alarm and may be late for our appointment.
''')

group('Home and chores', '''
E|洗濯物を外に干します。|せんたくもの を そと に ほします|I'll hang the laundry outside.
E|冷蔵庫に卵があります。|れいぞうこ に たまご が あります|There are eggs in the fridge.
E|部屋を少し片づけます。|へや を すこし かたづけます|I'll tidy the room a little.
E|今夜は家で料理します。|こんや は いえ で りょうり します|I'll cook at home tonight.
E|鍵は机の上です。|かぎ は つくえ の うえ です|The keys are on the desk.
M|ごみを出す日は水曜日ですよね。|ごみ を だす ひ は すいようび です よね|Wednesday is trash day, right?
M|この電球は切れているので交換します。|この でんきゅう は きれて いる ので こうかん します|This light bulb is out, so I'll replace it.
M|雨が降る前に洗濯物を取り込みましょう。|あめ が ふる まえ に せんたくもの を とりこみましょう|Let's bring in the laundry before it rains.
M|夕食の後で食器を洗ってもらえますか。|ゆうしょく の あと で しょっき を あらって もらえます か|Could you wash the dishes after dinner?
M|掃除機の音が大きいので、昼間に掃除します。|そうじき の おと が おおきい ので ひるま に そうじ します|The vacuum is loud, so I clean during the day.
M|買い物リストを冷蔵庫に貼っておきました。|かいもの りすと を れいぞうこ に はって おきました|I put the shopping list on the fridge.
M|この棚は一人で動かすには重すぎます。|この たな は ひとり で うごかす には おもすぎます|This shelf is too heavy to move alone.
H|部屋を使い終わったら、電気を消すようにしてください。|へや を つかいおわったら でんき を けす ように して ください|Please make a habit of turning off the lights after using a room.
H|引っ越しの準備を始めたものの、まだ荷物がたくさん残っています。|ひっこし の じゅんび を はじめた ものの まだ にもつ が たくさん のこって います|Although I've started packing to move, there's still a lot left.
H|水道の調子が悪いので、管理会社に連絡したほうがよさそうです。|すいどう の ちょうし が わるい ので かんりがいしゃ に れんらく した ほう が よさそう です|The plumbing isn't working well, so we'd better contact the property manager.
''')

group('Learning Japanese', '''
E|今日は漢字を五つ覚えます。|きょう は かんじ を いつつ おぼえます|I'll learn five kanji today.
E|この言葉を声に出します。|この ことば を こえ に だします|I'll say this word aloud.
E|日本語の日記を書いています。|にほんご の にっき を かいて います|I'm writing a diary in Japanese.
E|新しい単語を復習します。|あたらしい たんご を ふくしゅう します|I'll review new vocabulary.
E|今日は発音を練習したいです。|きょう は はつおん を れんしゅう したい です|I want to practise pronunciation today.
M|この漢字は読み方が二つあるそうです。|この かんじ は よみかた が ふたつ ある そう です|I hear this kanji has two readings.
M|例文を作ると単語を覚えやすくなります。|れいぶん を つくる と たんご を おぼえやすく なります|Making example sentences makes words easier to remember.
M|録音を聞いて、自分の発音を確かめます。|ろくおん を きいて じぶん の はつおん を たしかめます|I listen to my recording to check my pronunciation.
M|昨日覚えた表現を会話で使ってみました。|きのう おぼえた ひょうげん を かいわ で つかって みました|I tried using an expression I learned yesterday in conversation.
M|少し難しくても、最後まで聞いてみます。|すこし むずかしくても さいご まで きいて みます|Even if it's a bit difficult, I'll listen until the end.
M|この文章をもう少し自然に言えますか。|この ぶんしょう を もう すこし しぜん に いえます か|Can this sentence be said more naturally?
M|知らない言葉が出たら、文脈から意味を考えます。|しらない ことば が でたら ぶんみゃく から いみ を かんがえます|When I find an unfamiliar word, I guess its meaning from context.
H|正しく話すことばかり気にせず、まず伝えてみたいです。|ただしく はなす こと ばかり きにせず まず つたえて みたい です|I want to focus on communicating first rather than only speaking perfectly.
H|聞き取れなかった部分を何度も再生して確認しました。|ききとれなかった ぶぶん を なんど も さいせい して かくにん しました|I replayed the part I couldn't catch several times to check it.
H|毎日少しずつ練習すれば、自然に言葉が出てくるようになります。|まいにち すこしずつ れんしゅう すれば しぜん に ことば が でてくる ように なります|With a little daily practice, words start coming naturally.
''')

group('Making friends', '''
E|週末は友達と会います。|しゅうまつ は ともだち と あいます|I'm meeting a friend this weekend.
E|今日は一緒に帰りませんか。|きょう は いっしょ に かえりません か|Shall we head home together today?
E|その写真、いいですね。|その しゃしん いい です ね|That's a nice photo.
E|昨日は楽しかったです。|きのう は たのしかった です|Yesterday was fun.
E|また連絡しますね。|また れんらく します ね|I'll get in touch again.
M|新しくできたカフェに行ってみませんか。|あたらしく できた かふぇ に いって みません か|Would you like to try the new café?
M|もし時間があれば、映画の後でお茶しましょう。|もし じかん が あれば えいが の あと で おちゃ しましょう|If you have time, let's have tea after the movie.
M|その話の続き、今度ぜひ聞かせてください。|その はなし の つづき こんど ぜひ きかせて ください|Please tell me the rest of that story sometime.
M|初めて来たので、いろいろ教えてくれるとうれしいです。|はじめて きた ので いろいろ おしえて くれる と うれしい です|It's my first time here, so I'd be glad if you could show me around.
M|集合場所が変わったら、メッセージを送ります。|しゅうごうばしょ が かわったら めっせーじ を おくります|If the meeting place changes, I'll send a message.
M|この辺でおすすめのお店を知っていますか。|この へん で おすすめ の おみせ を しって います か|Do you know any good shops around here?
M|来週の予定が決まったら、また相談しましょう。|らいしゅう の よてい が きまったら また そうだん しましょう|Let's talk again when next week's plans are decided.
H|予定を合わせるのが難しそうなので、別の日にしませんか。|よてい を あわせる の が むずかしそう なので べつ の ひ に しません か|Our schedules seem hard to match, so shall we pick another day?
H|初対面なのに話しやすくて、時間がたつのを忘れました。|しょたいめん なのに はなしやすくて じかん が たつ の を わすれました|Even though we'd just met, talking was so easy I lost track of time.
H|誘ってくれてありがとう。今回は行けないけれど、次は参加したいです。|さそって くれて ありがとう こんかい は いけない けれど つぎ は さんか したい です|Thanks for inviting me. I can't make it this time, but I'd like to join next time.
''')

group('Campus and classroom', '''
E|教室は三階にあります。|きょうしつ は さんがい に あります|The classroom is on the third floor.
E|今日は宿題を出します。|きょう は しゅくだい を だします|I'll hand in my homework today.
E|この席を使ってもいいですか。|この せき を つかっても いい です か|May I use this seat?
E|次は数学の授業です。|つぎ は すうがく の じゅぎょう です|Math is the next class.
E|先生に質問があります。|せんせい に しつもん が あります|I have a question for the teacher.
M|ノートを忘れたので、紙を一枚借りてもいいですか。|のーと を わすれた ので かみ を いちまい かりても いい です か|I forgot my notebook; may I borrow a sheet of paper?
M|発表の順番はまだ決まっていません。|はっぴょう の じゅんばん は まだ きまって いません|The presentation order hasn't been decided yet.
M|グループで話し合ってから答えを発表しましょう。|ぐるーぷ で はなしあって から こたえ を はっぴょう しましょう|Let's discuss in groups before presenting our answers.
M|試験が終わったら図書館で勉強する予定です。|しけん が おわったら としょかん で べんきょう する よてい です|I plan to study in the library after the exam.
M|この問題の解き方を別の方法で説明できますか。|この もんだい の ときかた を べつ の ほうほう で せつめい できます か|Can you explain another way to solve this problem?
M|授業が始まるまであと十分あります。|じゅぎょう が はじまる まで あと じゅっぷん あります|There are ten minutes until class starts.
M|提出期限をもう一度確認したいです。|ていしゅつきげん を もういちど かくにん したい です|I'd like to double-check the submission deadline.
H|体調が悪くて欠席したので、授業の内容を教えてもらえますか。|たいちょう が わるくて けっせき した ので じゅぎょう の ないよう を おしえて もらえます か|I missed class because I felt ill. Could you tell me what was covered?
H|意見が違っていても、相手の説明を最後まで聞くことが大切です。|いけん が ちがって いても あいて の せつめい を さいご まで きく こと が たいせつ です|Even when we disagree, it's important to hear the other person's full explanation.
H|発表資料を前日までに共有していただけると助かります。|はっぴょうしりょう を ぜんじつ まで に きょうゆう して いただける と たすかります|It would help if you could share the presentation materials by the previous day.
''')

group('Work and meetings', '''
E|今日は午後から会議です。|きょう は ごご から かいぎ です|There's a meeting this afternoon.
E|今、資料を作っています。|いま しりょう を つくって います|I'm preparing the documents now.
E|昼休みは十二時からです。|ひるやすみ は じゅうにじ から です|Lunch break starts at twelve.
E|このメールを確認します。|この めーる を かくにん します|I'll check this email.
E|明日は在宅勤務です。|あした は ざいたくきんむ です|I'm working from home tomorrow.
M|会議の開始時間が三十分遅くなりました。|かいぎ の かいしじかん が さんじゅっぷん おそく なりました|The meeting start has been delayed by thirty minutes.
M|質問があれば、途中でも遠慮なく聞いてください。|しつもん が あれば とちゅう でも えんりょ なく きいて ください|If you have questions, feel free to ask at any time.
M|この資料は金曜日までに修正する予定です。|この しりょう は きんようび まで に しゅうせい する よてい です|I plan to revise these documents by Friday.
M|画面が見えにくいので、少し大きくできますか。|がめん が みにくい ので すこし おおきく できます か|The screen is hard to see. Can you enlarge it?
M|先ほど送ったメールにファイルを添付しました。|さきほど おくった めーる に ふぁいる を てんぷ しました|I attached a file to the email I sent earlier.
M|その件については担当者に確認してみます。|その けん について は たんとうしゃ に かくにん して みます|I'll check with the person responsible about that.
M|予定どおり進んでいるか教えてください。|よてい どおり すすんで いる か おしえて ください|Please tell me whether things are on schedule.
H|急な変更で申し訳ありませんが、打ち合わせを明日に延期できますか。|きゅうな へんこう で もうしわけ ありません が うちあわせ を あした に えんき できます か|I'm sorry for the sudden change, but could we move our meeting to tomorrow?
H|いただいたご意見を踏まえて、提案書を見直したいと思います。|いただいた ごいけん を ふまえて ていあんしょ を みなおしたい と おもいます|I'd like to revise the proposal based on your feedback.
H|準備に時間がかかっているため、結果の共有は来週になる見込みです。|じゅんび に じかん が かかって いる ため けっか の きょうゆう は らいしゅう に なる みこみ です|Preparation is taking time, so we expect to share the results next week.
''')

group('Cafés and restaurants', '''
E|今日はうどんが食べたいです。|きょう は うどん が たべたい です|I feel like eating udon today.
E|温かいお茶をください。|あたたかい おちゃ を ください|I'd like some hot tea, please.
E|ここで食べていきます。|ここ で たべて いきます|I'll eat here.
E|デザートは後で選びます。|でざーと は あと で えらびます|I'll choose dessert later.
E|このスープはおいしいです。|この すーぷ は おいしい です|This soup is delicious.
M|辛いものが苦手なので、辛さを控えめにできますか。|からい もの が にがて なので からさ を ひかえめ に できます か|I'm not good with spicy food. Can you make it mild?
M|友達がまだ来ていないので、先に飲み物だけ注文します。|ともだち が まだ きて いない ので さき に のみもの だけ ちゅうもん します|My friend isn't here yet, so I'll just order a drink first.
M|卵が入っていない料理を探しています。|たまご が はいって いない りょうり を さがして います|I'm looking for a dish without eggs.
M|食べきれなかった分を持ち帰ることはできますか。|たべきれなかった ぶん を もちかえる こと は できます か|May I take home what I couldn't finish?
M|このパンは焼きたてですか。|この ぱん は やきたて です か|Is this bread freshly baked?
M|あと五分で友達が来るので、少し待ってもらえますか。|あと ごふん で ともだち が くる ので すこし まって もらえます か|My friend will arrive in five minutes. Could you wait a little?
M|飲み物は氷なしでお願いします。|のみもの は こおり なし で おねがい します|I'd like my drink without ice, please.
H|予約の人数が一人増えたのですが、席を変更していただけますか。|よやく の にんずう が ひとり ふえた の です が せき を へんこう して いただけます か|One more person is joining our reservation. Could you adjust the seating?
H|アレルギーがあるため、調理に使う材料を確認させてください。|あれるぎー が ある ため ちょうり に つかう ざいりょう を かくにん させて ください|I have an allergy, so please let me check the ingredients used.
H|注文した飲み物がまだ届いていないようなので、確認をお願いできますか。|ちゅうもん した のみもの が まだ とどいて いない よう なので かくにん を おねがい できます か|My drink doesn't seem to have arrived yet. Could you please check?
''')

group('Groceries and cooking', '''
E|りんごを三つ買います。|りんご を みっつ かいます|I'll buy three apples.
E|今日の野菜は新鮮です。|きょう の やさい は しんせん です|Today's vegetables are fresh.
E|牛乳はどこにありますか。|ぎゅうにゅう は どこ に あります か|Where is the milk?
E|夕飯にカレーを作ります。|ゆうはん に かれー を つくります|I'll make curry for dinner.
E|買い物袋を持ってきました。|かいものぶくろ を もって きました|I brought my shopping bag.
M|このトマトは少し柔らかくなっています。|この とまと は すこし やわらかく なって います|These tomatoes have gotten a little soft.
M|レシピには玉ねぎが二個必要だと書いてあります。|れしぴ には たまねぎ が にこ ひつよう だ と かいて あります|The recipe says we need two onions.
M|冷凍食品は最後にかごに入れましょう。|れいとうしょくひん は さいご に かご に いれましょう|Let's put the frozen food in the basket last.
M|使い切れそうにないので、小さい袋を選びます。|つかいきれそう に ない ので ちいさい ふくろ を えらびます|I won't use it all, so I'll choose the smaller bag.
M|この豆腐はいつまで食べられますか。|この とうふ は いつ まで たべられます か|Until when is this tofu safe to eat?
M|にんじんを細く切ってから炒めます。|にんじん を ほそく きって から いためます|I'll slice the carrots thinly before frying them.
M|今夜の料理には何を入れる予定ですか。|こんや の りょうり には なに を いれる よてい です か|What are you planning to put in tonight's dish?
H|余った野菜を無駄にしないように、週末にスープを作ろうと思います。|あまった やさい を むだ に しない ように しゅうまつ に すーぷ を つくろう と おもいます|I plan to make soup this weekend so the leftover vegetables don't go to waste.
H|塩を入れすぎてしまったので、少し水を足して味を調整します。|しお を いれすぎて しまった ので すこし みず を たして あじ を ちょうせい します|I added too much salt, so I'll add some water to adjust the taste.
H|今週は外食を減らして、できるだけ自分でご飯を作ることにしました。|こんしゅう は がいしょく を へらして できるだけ じぶん で ごはん を つくる こと に しました|I've decided to eat out less and cook for myself as much as possible this week.
''')

group('Clothes and shopping', '''
E|青いシャツを探しています。|あおい しゃつ を さがして います|I'm looking for a blue shirt.
E|この靴は少し小さいです。|この くつ は すこし ちいさい です|These shoes are a little small.
E|違う色もありますか。|ちがう いろ も あります か|Does it come in another color?
E|今日は何も買いません。|きょう は なにも かいません|I'm not buying anything today.
E|この帽子が気に入りました。|この ぼうし が きにいりました|I like this hat.
M|もう少し軽いバッグを見せていただけますか。|もう すこし かるい ばっぐ を みせて いただけます か|Could you show me a slightly lighter bag?
M|この服は家で洗っても大丈夫ですか。|この ふく は いえ で あらっても だいじょうぶ です か|Is it okay to wash this clothing at home?
M|サイズが合わなかったので、交換できるか聞いてみます。|さいず が あわなかった ので こうかん できる か きいて みます|The size didn't fit, so I'll ask if I can exchange it.
M|友達への誕生日プレゼントを選んでいます。|ともだち への たんじょうびぷれぜんと を えらんで います|I'm choosing a birthday gift for my friend.
M|表示されている値段には税金が含まれていますか。|ひょうじ されて いる ねだん には ぜいきん が ふくまれて います か|Does the displayed price include tax?
M|この商品は来月もう一度入荷しますか。|この しょうひん は らいげつ もういちど にゅうか します か|Will this item be restocked next month?
M|雨の日でも使える靴が欲しいです。|あめ の ひ でも つかえる くつ が ほしい です|I want shoes I can wear on rainy days.
H|購入した商品に不具合があったため、返品方法を教えていただけますか。|こうにゅう した しょうひん に ふぐあい が あった ため へんぴんほうほう を おしえて いただけます か|The item I bought is faulty. Could you explain how to return it?
H|予算を超えないように、必要なものから順番に買うことにしました。|よさん を こえない ように ひつような もの から じゅんばん に かう こと に しました|I've decided to buy the essentials first so I stay within budget.
H|実際に試してから決めたいので、少し考える時間をいただけますか。|じっさい に ためして から きめたい ので すこし かんがえる じかん を いただけます か|I'd like to try it before deciding. Could you give me a little time to think?
''')

group('Walking around town', '''
E|図書館まで歩きます。|としょかん まで あるきます|I'll walk to the library.
E|角に小さな花屋があります。|かど に ちいさな はなや が あります|There's a small flower shop on the corner.
E|この道は静かですね。|この みち は しずか です ね|This street is quiet, isn't it?
E|橋の向こうに公園があります。|はし の むこう に こうえん が あります|There's a park across the bridge.
E|ここから写真を撮ります。|ここ から しゃしん を とります|I'll take a photo from here.
M|次の交差点を右に曲がると郵便局が見えます。|つぎ の こうさてん を みぎ に まがる と ゆうびんきょく が みえます|Turn right at the next intersection and you'll see the post office.
M|この歩道は狭いので、ゆっくり歩きましょう。|この ほどう は せまい ので ゆっくり あるきましょう|This sidewalk is narrow, so let's walk slowly.
M|地図では近そうですが、坂が多いですね。|ちず では ちかそう です が さか が おおい です ね|It looks close on the map, but there are lots of hills.
M|信号を渡ったところで待ち合わせしましょう。|しんごう を わたった ところ で まちあわせ しましょう|Let's meet just after the traffic light.
M|この道を進むと海が見えると聞きました。|この みち を すすむ と うみ が みえる と ききました|I heard you can see the sea if you follow this road.
M|公園の入口は反対側にあるようです。|こうえん の いりぐち は はんたいがわ に ある よう です|The park entrance seems to be on the other side.
M|横断歩道があるところまで戻りましょう。|おうだんほどう が ある ところ まで もどりましょう|Let's go back to where the crosswalk is.
H|工事でいつもの道が通れなくなっているので、別の道を探しています。|こうじ で いつも の みち が とおれなく なって いる ので べつ の みち を さがして います|The usual road is closed for construction, so I'm finding another way.
H|急いでいないので、景色を楽しみながら遠回りしてみませんか。|いそいで いない ので けしき を たのしみながら とおまわり して みません か|We're not in a rush, so why don't we take a scenic detour?
H|初めての場所では、建物の名前も確認しながら歩くようにしています。|はじめて の ばしょ では たてもの の なまえ も かくにん しながら あるく ように しています|In unfamiliar places, I make a point of checking building names as I walk.
''')

group('Trains and stations', '''
E|今日は電車で行きます。|きょう は でんしゃ で いきます|I'll go by train today.
E|切符を買ってきます。|きっぷ を かって きます|I'll go buy a ticket.
E|次は渋谷駅です。|つぎ は しぶやえき です|The next stop is Shibuya Station.
E|あの電車は空いています。|あの でんしゃ は すいて います|That train isn't crowded.
E|ホームで友達を待ちます。|ほーむ で ともだち を まちます|I'll wait for my friend on the platform.
M|急行に乗ると二十分ほど早く着きます。|きゅうこう に のる と にじゅっぷん ほど はやく つきます|Taking the express gets us there about twenty minutes earlier.
M|乗り換え時間が短いので、先に出口を調べます。|のりかえじかん が みじかい ので さき に でぐち を しらべます|The transfer is tight, so I'll check the exit in advance.
M|この車両には大きな荷物を置ける場所がありますか。|この しゃりょう には おおきな にもつ を おける ばしょ が あります か|Is there a place for large luggage in this carriage?
M|電車が遅れているという案内が流れています。|でんしゃ が おくれて いる と いう あんない が ながれて います|An announcement says the train is delayed.
M|改札を出る前に交通系カードの残高を確認します。|かいさつ を でる まえ に こうつうけいかーど の ざんだか を かくにん します|I'll check my transit card balance before leaving the gates.
M|次の駅で降りるので、ドアの近くへ移動します。|つぎ の えき で おりる ので どあ の ちかく へ いどう します|I'm getting off at the next station, so I'll move closer to the door.
M|混雑していたため、一本後の電車にしました。|こんざつ して いた ため いっぽん あと の でんしゃ に しました|It was crowded, so I took the next train instead.
H|目的地までの運賃が分からなかったので、駅員さんに確認しました。|もくてきち まで の うんちん が わからなかった ので えきいんさん に かくにん しました|I didn't know the fare to my destination, so I checked with station staff.
H|乗り過ごしてしまった場合、どの駅で折り返せばいいでしょうか。|のりすごして しまった ばあい どの えき で おりかえせば いい でしょう か|If I miss my stop, which station should I use to turn back?
H|電車の運行状況が変わる可能性があるため、出発前に最新情報を確認します。|でんしゃ の うんこうじょうきょう が かわる かのうせい が ある ため しゅっぱつまえ に さいしんじょうほう を かくにん します|Service may change, so I'll check the latest train information before leaving.
''')

group('Trips and sightseeing', '''
E|明日は京都に行きます。|あした は きょうと に いきます|I'm going to Kyoto tomorrow.
E|この神社はとても静かです。|この じんじゃ は とても しずか です|This shrine is very peaceful.
E|旅行の写真を見せます。|りょこう の しゃしん を みせます|I'll show you my travel photos.
E|今日は博物館に行きたいです。|きょう は はくぶつかん に いきたい です|I want to visit a museum today.
E|お土産にお菓子を買いました。|おみやげ に おかし を かいました|I bought some sweets as souvenirs.
M|朝早く出発すると、観光する時間が増えます。|あさ はやく しゅっぱつ する と かんこう する じかん が ふえます|Leaving early gives us more time to sightsee.
M|この町の歴史について少し知りたいです。|この まち の れきし について すこし しりたい です|I'd like to learn a little about this town's history.
M|入場券はオンラインで予約しておきました。|にゅうじょうけん は おんらいん で よやく して おきました|I booked the admission tickets online.
M|混んでいる場所を避けて、静かな庭を散歩しました。|こんで いる ばしょ を さけて しずかな にわ を さんぽ しました|I avoided the crowds and walked through a quiet garden.
M|帰りのバスの時間を先に調べておきましょう。|かえり の ばす の じかん を さき に しらべて おきましょう|Let's check the return bus schedule first.
M|この景色が見られて本当にうれしいです。|この けしき が みられて ほんとうに うれしい です|I'm really happy I got to see this view.
M|写真を撮ってもいい場所かどうか確認しましょう。|しゃしん を とっても いい ばしょ か どうか かくにん しましょう|Let's check whether photography is allowed here.
H|予定を詰め込みすぎず、一つ一つの場所をゆっくり楽しみたいです。|よてい を つめこみすぎず ひとつ ひとつ の ばしょ を ゆっくり たのしみたい です|I'd rather enjoy each place slowly than cram too much into the itinerary.
H|雨が強くなった場合に備えて、屋内で楽しめる場所も探しておきました。|あめ が つよく なった ばあい に そなえて おくない で たのしめる ばしょ も さがして おきました|I also found indoor places in case the rain gets heavy.
H|地域の習慣を大切にしながら、地元の方々と交流できたらと思います。|ちいき の しゅうかん を たいせつ に しながら じもと の かたがた と こうりゅう できたら と おもいます|I hope to connect with local people while respecting local customs.
''')

group('Hotels and guesthouses', '''
E|今日から二泊します。|きょう から にはく します|I'm staying for two nights from today.
E|部屋は402号室です。|へや は よんまるに ごうしつ です|My room is number 402.
E|朝は七時に出ます。|あさ は しちじ に でます|I'll leave at seven in the morning.
E|タオルを一枚使います。|たおる を いちまい つかいます|I'll use one towel.
E|荷物はここに置きます。|にもつ は ここ に おきます|I'll leave my bags here.
M|チェックイン前に荷物を預けることはできますか。|ちぇっくいん まえ に にもつ を あずける こと は できます か|Can I leave my luggage before check-in?
M|静かな部屋が空いていれば、そちらを希望します。|しずかな へや が あいて いれば そちら を きぼう します|If a quiet room is available, I'd prefer that.
M|エアコンの温度を下げても部屋が涼しくなりません。|えあこん の おんど を さげても へや が すずしく なりません|The room won't cool down even when I lower the AC temperature.
M|朝食を食べない日は前日までに伝えます。|ちょうしょく を たべない ひ は ぜんじつ まで に つたえます|I'll let you know by the previous day if I won't have breakfast.
M|近くに早朝から開いているお店はありますか。|ちかく に そうちょう から あいて いる おみせ は あります か|Are any nearby shops open early in the morning?
M|部屋のカードキーが反応しなくなりました。|へや の かーどきー が はんのう しなく なりました|My room key card has stopped working.
M|明日は出発が早いので、今夜中に精算できますか。|あした は しゅっぱつ が はやい ので こんやじゅう に せいさん できます か|I'm leaving early tomorrow. Can I settle the bill tonight?
H|予約時にお願いした条件が反映されていないようなので、確認していただけますか。|よやくじ に おねがい した じょうけん が はんえい されて いない よう なので かくにん して いただけます か|The preferences I requested when booking don't seem to be reflected. Could you check?
H|急な予定変更で滞在を一日延ばす必要があるのですが、可能でしょうか。|きゅうな よていへんこう で たいざい を いちにち のばす ひつよう が ある の です が かのう でしょう か|My plans suddenly changed and I need one more night. Would that be possible?
H|夜間は廊下の声がよく聞こえるため、静かにしていただけると助かります。|やかん は ろうか の こえ が よく きこえる ため しずか に して いただける と たすかります|Voices in the corridor are clearly audible at night, so I'd appreciate some quiet.
''')

group('Money and payments', '''
E|今日は現金を使います。|きょう は げんきん を つかいます|I'll pay in cash today.
E|このカードで払います。|この かーど で はらいます|I'll pay with this card.
E|小銭を少し持っています。|こぜに を すこし もって います|I have some coins.
E|予算は三千円です。|よさん は さんぜんえん です|My budget is three thousand yen.
E|財布はかばんの中です。|さいふ は かばん の なか です|My wallet is in my bag.
M|支払いが完了したか画面で確認します。|しはらい が かんりょう した か がめん で かくにん します|I'll check the screen to see whether payment went through.
M|友達と昼食代を半分ずつ出しました。|ともだち と ちゅうしょくだい を はんぶんずつ だしました|My friend and I split the lunch bill equally.
M|今日は使いすぎたので、明日は節約します。|きょう は つかいすぎた ので あした は せつやく します|I spent too much today, so I'll save money tomorrow.
M|こちらの機械は交通系カードにも対応していますか。|こちら の きかい は こうつうけいかーど にも たいおう して います か|Does this machine accept transit cards too?
M|一度に大きなお金を両替しないようにしています。|いちど に おおきな おかね を りょうがえ しない ように しています|I try not to exchange large amounts at once.
M|領収書はメールで送っていただけますか。|りょうしゅうしょ は めーる で おくって いただけます か|Could you send the receipt by email?
M|金額が予想より高かったので内訳を確認します。|きんがく が よそう より たかかった ので うちわけ を かくにん します|The total was higher than expected, so I'll check the breakdown.
H|二重に請求された可能性があるため、取引履歴を確認していただけますか。|にじゅう に せいきゅう された かのうせい が ある ため とりひきりれき を かくにん して いただけます か|I may have been charged twice. Could you check the transaction history?
H|返金されるまでにどのくらい時間がかかるか教えていただきたいです。|へんきん される まで に どのくらい じかん が かかる か おしえて いただきたい です|I'd like to know roughly how long the refund will take.
H|万が一カードを紛失した場合に備え、連絡先を控えておきました。|まんがいち かーど を ふんしつ した ばあい に そなえ れんらくさき を ひかえて おきました|I saved the contact details in case I ever lose my card.
''')

group('Phone and internet', '''
E|今、電話に出られません。|いま でんわ に でられません|I can't answer the phone right now.
E|写真を送りますね。|しゃしん を おくります ね|I'll send you the photos.
E|充電がもうすぐ切れます。|じゅうでん が もうすぐ きれます|My battery is almost dead.
E|パスワードを変えました。|ぱすわーど を かえました|I changed my password.
E|今日は動画を見ます。|きょう は どうが を みます|I'll watch a video today.
M|電波が弱いので、窓の近くに移動します。|でんぱ が よわい ので まど の ちかく に いどう します|The signal is weak, so I'll move closer to the window.
M|通知が多すぎるので、いくつかオフにしました。|つうち が おおすぎる ので いくつか おふ に しました|There were too many notifications, so I turned some off.
M|このアプリでは発音の練習もできます。|この あぷり では はつおん の れんしゅう も できます|You can also practise pronunciation in this app.
M|メッセージが届いたら、時間のあるときに返信します。|めっせーじ が とどいたら じかん の ある とき に へんしん します|I'll reply when I have time after your message arrives.
M|インターネットにつながらないので、設定を確認しています。|いんたーねっと に つながらない ので せってい を かくにん して います|I'm checking the settings because I can't connect to the internet.
M|大切な写真は別の場所にも保存しておきます。|たいせつな しゃしん は べつ の ばしょ にも ほぞん して おきます|I'll also back up important photos somewhere else.
M|画面が固まったので、一度アプリを再起動します。|がめん が かたまった ので いちど あぷり を さいきどう します|The screen froze, so I'll restart the app.
H|個人情報を送る前に、相手が信頼できるか確認するようにしています。|こじんじょうほう を おくる まえ に あいて が しんらい できる か かくにん する ように しています|Before sharing personal information, I check that the recipient is trustworthy.
H|接続が不安定なため、会議に戻れなかったら電話で連絡します。|せつぞく が ふあんていな ため かいぎ に もどれなかったら でんわ で れんらく します|My connection is unstable; if I can't rejoin the meeting, I'll call.
H|自動翻訳だけでは意味が伝わらないこともあるので、表現を確かめます。|じどうほんやく だけ では いみ が つたわらない こと も ある ので ひょうげん を たしかめます|Automatic translation doesn't always convey the meaning, so I check the wording.
''')

group('Weather and outdoor plans', '''
E|今日は風が強いです。|きょう は かぜ が つよい です|It's windy today.
E|空に雲が増えました。|そら に くも が ふえました|There are more clouds in the sky now.
E|傘を持っていきます。|かさ を もって いきます|I'll take an umbrella.
E|夕方は涼しくなります。|ゆうがた は すずしく なります|It gets cooler in the evening.
E|明日は晴れるといいですね。|あした は はれる と いい です ね|I hope it's sunny tomorrow.
M|天気がよければ、自転車で川沿いを走ります。|てんき が よければ じてんしゃ で かわぞい を はしります|If the weather's good, I'll cycle along the river.
M|午後から雨の予報なので、洗濯は明日にします。|ごご から あめ の よほう なので せんたく は あした に します|Rain is forecast for the afternoon, so I'll do laundry tomorrow.
M|山の上は寒そうだから、上着を持っていこう。|やま の うえ は さむそう だから うわぎ を もって いこう|It looks cold on the mountain, so let's bring jackets.
M|暑い日は水分をこまめに取るようにしています。|あつい ひ は すいぶん を こまめ に とる ように しています|On hot days, I make sure to drink water regularly.
M|天気予報を見てからピクニックの日を決めます。|てんきよほう を みて から ぴくにっく の ひ を きめます|We'll choose the picnic day after checking the forecast.
M|雨がやんだら、犬と散歩に出かけます。|あめ が やんだら いぬ と さんぽ に でかけます|When it stops raining, I'll go for a walk with the dog.
M|朝と夜の気温差が大きいので、服装に気をつけます。|あさ と よる の きおんさ が おおきい ので ふくそう に きをつけます|The temperature changes a lot between morning and night, so I'll dress accordingly.
H|急に天候が変わることもあるので、山に行く前に安全情報を調べます。|きゅうに てんこう が かわる こと も ある ので やま に いく まえ に あんぜんじょうほう を しらべます|Mountain weather can change suddenly, so I check safety information before going.
H|雨天の場合は屋外イベントが中止になる可能性があります。|うてん の ばあい は おくがいいべんと が ちゅうし に なる かのうせい が あります|The outdoor event may be cancelled if it rains.
H|せっかく遠くまで来たのに、霧で景色がほとんど見えませんでした。|せっかく とおく まで きた のに きり で けしき が ほとんど みえません でした|We came all this way, but the fog hid almost all the view.
''')

group('Hobbies and weekends', '''
E|週末は絵を描きます。|しゅうまつ は え を かきます|I draw on weekends.
E|最近、料理が楽しいです。|さいきん りょうり が たのしい です|I've been enjoying cooking lately.
E|毎晩少し本を読みます。|まいばん すこし ほん を よみます|I read a little every night.
E|昨日、新しい曲を聞きました。|きのう あたらしい きょく を ききました|I listened to a new song yesterday.
E|休みの日は自転車に乗ります。|やすみ の ひ は じてんしゃ に のります|I cycle on my days off.
M|週末に撮った写真を整理しています。|しゅうまつ に とった しゃしん を せいり して います|I'm sorting the photos I took this weekend.
M|時間があるときは簡単なパンを焼いています。|じかん が ある とき は かんたんな ぱん を やいて います|When I have time, I bake simple bread.
M|ギターを始めたばかりなので、まだ練習中です。|ぎたー を はじめた ばかり なので まだ れんしゅうちゅう です|I've only just started guitar, so I'm still practising.
M|試合を見るのも好きですが、実際に体を動かすほうが好きです。|しあい を みる の も すき です が じっさい に からだ を うごかす ほう が すき です|I like watching games, but I prefer being active myself.
M|最近は植物を育てることに興味があります。|さいきん は しょくぶつ を そだてる こと に きょうみ が あります|Lately I've become interested in growing plants.
M|仕事の後に短い散歩をすると気分が変わります。|しごと の あと に みじかい さんぽ を する と きぶん が かわります|A short walk after work helps me reset.
M|今度の休みには陶芸教室に参加してみたいです。|こんど の やすみ には とうげいきょうしつ に さんか して みたい です|I'd like to join a pottery class on my next day off.
H|新しい趣味を始めるときは、上手になることより楽しむことを大切にしています。|あたらしい しゅみ を はじめる とき は じょうず に なる こと より たのしむ こと を たいせつ に しています|When starting a hobby, I value having fun more than becoming skilled.
H|忙しくても週に一度は趣味の時間を取るようにしています。|いそがしくても しゅう に いちど は しゅみ の じかん を とる ように しています|Even when I'm busy, I try to make time for my hobby once a week.
H|難しそうだと思っていたことでも、実際にやってみると意外に面白いものです。|むずかしそう だ と おもって いた こと でも じっさい に やって みる と いがい に おもしろい もの です|Even something that looks difficult can be surprisingly fun when you try it.
''')

group('Health and wellbeing', '''
E|今日は少し疲れています。|きょう は すこし つかれて います|I'm a little tired today.
E|早めに寝るつもりです。|はやめ に ねる つもり です|I plan to go to bed early.
E|今日は散歩だけにします。|きょう は さんぽ だけ に します|I'll just go for a walk today.
E|水を飲んで休みます。|みず を のんで やすみます|I'll drink some water and rest.
E|頭が少し痛いです。|あたま が すこし いたい です|I have a mild headache.
M|昨日からのどが痛いので、今日は家で休みます。|きのう から のど が いたい ので きょう は いえ で やすみます|My throat has hurt since yesterday, so I'm resting at home.
M|具合がよくないので、予約した予定を変更したいです。|ぐあい が よくない ので よやく した よてい を へんこう したい です|I'm not feeling well, so I'd like to change my appointment.
M|この薬は食事の前に飲むものですか。|この くすり は しょくじ の まえ に のむ もの です か|Is this medicine meant to be taken before meals?
M|よく眠れるように、寝る前は携帯を見ないようにしています。|よく ねむれる ように ねる まえ は けいたい を みない ように しています|To sleep better, I try not to look at my phone before bed.
M|熱が続いているので、病院に相談しようと思います。|ねつ が つづいて いる ので びょういん に そうだん しよう と おもいます|My fever has continued, so I think I'll contact a clinic.
M|無理をせず、今日は早めに帰ってください。|むり を せず きょう は はやめ に かえって ください|Please don't push yourself; go home early today.
M|体調が戻るまで激しい運動は控えます。|たいちょう が もどる まで はげしい うんどう は ひかえます|I'll avoid intense exercise until I'm feeling better.
H|症状がいつから始まったのか、順番に説明してもよろしいでしょうか。|しょうじょう が いつ から はじまった の か じゅんばん に せつめい しても よろしい でしょう か|May I explain step by step when my symptoms started?
H|以前に同じ薬で体調を崩したことがあるので、別の方法を相談したいです。|いぜん に おなじ くすり で たいちょう を くずした こと が ある ので べつ の ほうほう を そうだん したい です|I've had a bad reaction to the same medicine before, so I'd like to discuss alternatives.
H|体調に変化があった場合は、自己判断せずに医療機関へ連絡します。|たいちょう に へんか が あった ばあい は じこはんだん せず に いりょうきかん へ れんらく します|If my condition changes, I'll contact a healthcare provider rather than decide alone.
''')

group('Solving everyday problems', '''
E|傘をどこかに忘れました。|かさ を どこか に わすれました|I left my umbrella somewhere.
E|このドアが開きません。|この どあ が あきません|This door won't open.
E|水が出なくなりました。|みず が でなく なりました|The water stopped running.
E|道を間違えました。|みち を まちがえました|I took the wrong road.
E|少し困っています。|すこし こまって います|I'm having a bit of trouble.
M|レジで違う商品を受け取ったようです。|れじ で ちがう しょうひん を うけとった よう です|I seem to have received the wrong item at checkout.
M|地図の場所と実際の入口が違うみたいです。|ちず の ばしょ と じっさい の いりぐち が ちがう みたい です|The entrance seems to be in a different place from the map.
M|自転車のタイヤに空気が入っていません。|じてんしゃ の たいや に くうき が はいって いません|My bicycle tire doesn't have enough air.
M|鍵をなくしたかもしれないので、来た道を戻ります。|かぎ を なくした かも しれない ので きた みち を もどります|I may have lost my keys, so I'll retrace my steps.
M|約束の時間を勘違いしてしまいました。|やくそく の じかん を かんちがい して しまいました|I misunderstood the time we agreed on.
M|困ったときに相談できる人がいて安心しました。|こまった とき に そうだん できる ひと が いて あんしん しました|I felt relieved to have someone to ask for help.
M|まず何が起きたのか落ち着いて確認します。|まず なに が おきた の か おちついて かくにん します|First I'll calmly check what happened.
H|状況を正しく伝えたいので、最初から説明させていただけますか。|じょうきょう を ただしく つたえたい ので さいしょ から せつめい させて いただけます か|I want to explain the situation accurately, so may I start from the beginning?
H|案内に書かれていた手順を試したのですが、問題が解決しませんでした。|あんない に かかれて いた てじゅん を ためした の です が もんだい が かいけつ しません でした|I followed the instructions, but the problem wasn't resolved.
H|同じ問題が再び起きないように、原因と対策を記録しておきます。|おなじ もんだい が ふたたび おきない ように げんいん と たいさく を きろく して おきます|I'll record the cause and solution so the same issue doesn't happen again.
''')

group('Safety and asking for help', '''
E|こちらは危険です。|こちら は きけん です|It's dangerous here.
E|少し離れてください。|すこし はなれて ください|Please step back a little.
E|この道は通れません。|この みち は とおれません|This road is closed.
E|子どもが泣いています。|こども が ないて います|A child is crying.
E|係の人を呼びます。|かかり の ひと を よびます|I'll call a staff member.
M|階段が滑りやすいので、手すりを使ってください。|かいだん が すべりやすい ので てすり を つかって ください|The stairs are slippery, so please use the handrail.
M|ここで具合が悪くなった人がいるので、手伝ってください。|ここ で ぐあい が わるく なった ひと が いる ので てつだって ください|Someone here has become unwell. Please help.
M|この建物の避難場所はどこにありますか。|この たてもの の ひなんばしょ は どこ に あります か|Where is the evacuation area for this building?
M|忘れ物が見つかったら、この番号に連絡してください。|わすれもの が みつかったら この ばんごう に れんらく して ください|If the lost item is found, please call this number.
M|地震の後はエレベーターを使わないでください。|じしん の あと は えれべーたー を つかわない で ください|Please don't use the elevator after an earthquake.
M|友達と離れてしまったので、待ち合わせ場所へ戻ります。|ともだち と はなれて しまった ので まちあわせばしょ へ もどります|I got separated from my friend, so I'll return to our meeting point.
M|けがをした人がいる場合は、すぐに専門の人に知らせましょう。|けが を した ひと が いる ばあい は すぐに せんもん の ひと に しらせましょう|If someone is injured, let's alert trained personnel immediately.
H|緊急の対応が必要かもしれないので、今の状況を詳しく伝えます。|きんきゅう の たいおう が ひつよう かも しれない ので いま の じょうきょう を くわしく つたえます|Urgent help may be needed, so I'll explain the situation in detail.
H|本人の意識があるかどうか確認し、指示を受けながら行動します。|ほんにん の いしき が ある か どうか かくにん し しじ を うけながら こうどう します|I'll check whether the person is conscious and follow instructions.
H|安全が確認できるまでは、無理に現場へ近づかないようにしてください。|あんぜん が かくにん できる まで は むりに げんば へ ちかづかない ように して ください|Please don't approach the area until it has been confirmed safe.
''')

group('Family and neighbours', '''
E|母に電話をかけます。|はは に でんわ を かけます|I'll call my mother.
E|祖父は庭にいます。|そふ は にわ に います|My grandfather is in the garden.
E|妹と買い物に行きます。|いもうと と かいもの に いきます|I'll go shopping with my younger sister.
E|近所の人に会いました。|きんじょ の ひと に あいました|I met a neighbor.
E|みんなで夕食を食べます。|みんな で ゆうしょく を たべます|We'll have dinner together.
M|家族と相談してから旅行の日程を決めます。|かぞく と そうだん して から りょこう の にってい を きめます|I'll discuss it with my family before setting the trip dates.
M|隣の家の方が荷物を運ぶのを手伝ってくれました。|となり の いえ の かた が にもつ を はこぶ の を てつだって くれました|Our neighbor helped carry the luggage.
M|今度の日曜日に親戚が遊びに来る予定です。|こんど の にちようび に しんせき が あそび に くる よてい です|Relatives are coming to visit this Sunday.
M|子どもたちは公園で元気に遊んでいます。|こどもたち は こうえん で げんき に あそんで います|The children are happily playing in the park.
M|忙しいときはお互いに助け合うことにしています。|いそがしい とき は おたがい に たすけあう こと に しています|We try to help each other when we're busy.
M|お隣さんが旅行中なので、植物に水をあげています。|おとなりさん が りょこうちゅう なので しょくぶつ に みず を あげて います|Our neighbor is traveling, so I'm watering their plants.
M|家族の誕生日を忘れないように予定表に入れました。|かぞく の たんじょうび を わすれない ように よていひょう に いれました|I added the family's birthdays to my calendar so I don't forget.
H|生活の時間帯が違うので、家ではお互いの睡眠を邪魔しないようにしています。|せいかつ の じかんたい が ちがう ので いえ では おたがい の すいみん を じゃま しない ように しています|Our routines differ, so we try not to disturb each other's sleep at home.
H|近所の行事に参加したおかげで、今まで知らなかった人と知り合えました。|きんじょ の ぎょうじ に さんか した おかげ で いままで しらなかった ひと と しりあえました|Joining a neighborhood event helped me meet people I hadn't known.
H|何か困ったことがあれば遠慮せずに声をかけてほしいと伝えました。|なにか こまった こと が あれば えんりょ せず に こえ を かけて ほしい と つたえました|I told them not to hesitate to ask if they need help.
''')

group('Japanese manners and culture', '''
E|玄関で靴を脱ぎます。|げんかん で くつ を ぬぎます|I'll take off my shoes at the entrance.
E|ここでは静かに話します。|ここ では しずか に はなします|I'll speak quietly here.
E|お祭りの音が聞こえます。|おまつり の おと が きこえます|I can hear the festival sounds.
E|神社の前で立ち止まります。|じんじゃ の まえ で たちどまります|I'll stop in front of the shrine.
E|今日は和菓子を食べました。|きょう は わがし を たべました|I ate traditional Japanese sweets today.
M|人が多い場所では、荷物を前に持つようにしています。|ひと が おおい ばしょ では にもつ を まえ に もつ ように しています|In crowded places, I keep my bag in front of me.
M|このお店では靴を脱いでから席に上がります。|この おみせ では くつ を ぬいで から せき に あがります|At this restaurant, you take off your shoes before going to your seat.
M|お寺を見学するときは、周りの人の邪魔にならないようにします。|おてら を けんがく する とき は まわり の ひと の じゃま に ならない ように します|When visiting a temple, I try not to disturb others.
M|写真を撮る前に、その場所のルールを確認します。|しゃしん を とる まえ に その ばしょ の るーる を かくにん します|Before taking photos, I check the local rules.
M|季節によって違う行事があるのは面白いですね。|きせつ によって ちがう ぎょうじ が ある の は おもしろい です ね|It's interesting how festivals differ by season.
M|地域によって食べ物の味つけが違うそうです。|ちいき によって たべもの の あじつけ が ちがう そう です|I've heard seasoning varies by region.
M|知らない習慣があれば、失礼にならないように聞いてみます。|しらない しゅうかん が あれば しつれい に ならない ように きいて みます|If I don't know a custom, I'll ask so I don't cause offense.
H|文化の違いをすぐに判断せず、まず理由を知ろうとすることが大切だと思います。|ぶんか の ちがい を すぐに はんだん せず まず りゆう を しろう と する こと が たいせつ だ と おもいます|I think it's important to understand a cultural difference before judging it.
H|地域の方々に迷惑をかけないように、観光中も決まりを守って行動します。|ちいき の かたがた に めいわく を かけない ように かんこうちゅう も きまり を まもって こうどう します|I follow local rules while sightseeing to avoid inconveniencing residents.
H|初めて見る伝統行事だったので、その由来について詳しく調べてみました。|はじめて みる でんとうぎょうじ だった ので その ゆらい について くわしく しらべて みました|It was a traditional event I'd never seen, so I researched its origins.
''')

group('Plans and appointments', '''
E|次の約束は金曜日です。|つぎ の やくそく は きんようび です|Our next appointment is Friday.
E|明日は予定があります。|あした は よてい が あります|I have plans tomorrow.
E|三時に駅で会いましょう。|さんじ に えき で あいましょう|Let's meet at the station at three.
E|今週は少し忙しいです。|こんしゅう は すこし いそがしい です|I'm a little busy this week.
E|来月は時間があります。|らいげつ は じかん が あります|I have time next month.
M|予定が決まったら、カレンダーに書き込んでおきます。|よてい が きまったら かれんだー に かきこんで おきます|Once plans are settled, I'll put them in my calendar.
M|午後の予定が空いたので、早めに伺えます。|ごご の よてい が あいた ので はやめ に うかがえます|My afternoon is free now, so I can come earlier.
M|予約の時間を一時間後ろにずらせますか。|よやく の じかん を いちじかん うしろ に ずらせます か|Could we push the booking back by an hour?
M|交通状況によって到着時間が変わるかもしれません。|こうつうじょうきょう によって とうちゃくじかん が かわる かも しれません|My arrival time may change depending on traffic.
M|予定を変更するときは、早めに連絡するようにしています。|よてい を へんこう する とき は はやめ に れんらく する ように しています|I try to give early notice when changing plans.
M|午前中は仕事があるので、夕方なら大丈夫です。|ごぜんちゅう は しごと が ある ので ゆうがた なら だいじょうぶ です|I work in the morning, but the evening is fine.
M|お互いに都合のよい日を探しましょう。|おたがい に つごう の よい ひ を さがしましょう|Let's find a day that works for both of us.
H|今週中に終わらせる必要がある作業から優先して進めます。|こんしゅうじゅう に おわらせる ひつよう が ある さぎょう から ゆうせん して すすめます|I'll prioritize tasks that must be finished this week.
H|急な用事が入ってしまったため、予定を変更できないか相談しています。|きゅうな ようじ が はいって しまった ため よてい を へんこう できない か そうだん して います|Something urgent came up, so I'm asking whether we can reschedule.
H|先に移動時間を計算しておけば、無理のない予定を立てやすくなります。|さき に いどうじかん を けいさん して おけば むり の ない よてい を たてやすく なります|Planning travel time ahead makes it easier to schedule realistically.
''')

group('Nature and environment', '''
E|川の水がきれいです。|かわ の みず が きれい です|The river water is clear.
E|山に雪が残っています。|やま に ゆき が のこって います|There's still snow on the mountain.
E|公園で鳥を見ました。|こうえん で とり を みました|I saw a bird in the park.
E|今日は花に水をあげます。|きょう は はな に みず を あげます|I'll water the flowers today.
E|この木はとても大きいです。|この き は とても おおきい です|This tree is very big.
M|春になると、この道には桜が咲きます。|はる に なる と この みち には さくら が さきます|Cherry blossoms bloom along this street in spring.
M|使い捨ての容器を減らすため、水筒を持ち歩いています。|つかいすて の ようき を へらす ため すいとう を もちあるいて います|I carry a reusable bottle to reduce disposable containers.
M|夜は星がよく見える場所へ行ってみたいです。|よる は ほし が よく みえる ばしょ へ いって みたい です|I'd like to visit somewhere with a clear view of the stars at night.
M|海岸を歩きながら、落ちているごみを拾いました。|かいがん を あるきながら おちて いる ごみ を ひろいました|I picked up litter while walking along the beach.
M|植物の名前を調べるのが最近の楽しみです。|しょくぶつ の なまえ を しらべる の が さいきん の たのしみ です|Looking up plant names has become a recent pleasure of mine.
M|この池には小さな魚がたくさん泳いでいます。|この いけ には ちいさな さかな が たくさん およいで います|Lots of small fish are swimming in this pond.
M|自然を守るために、一人でもできることを続けたいです。|しぜん を まもる ため に ひとり でも できる こと を つづけたい です|I want to keep doing what I can to protect nature.
H|観光客が増えることで、地域の自然環境に負担がかかる場合もあります。|かんこうきゃく が ふえる こと で ちいき の しぜんかんきょう に ふたん が かかる ばあい も あります|More visitors can sometimes put pressure on the local environment.
H|季節ごとの変化を記録しておくと、小さな自然の違いにも気づくようになります。|きせつ ごと の へんか を きろく して おく と ちいさな しぜん の ちがい にも きづく ように なります|Recording seasonal changes helps us notice small differences in nature.
H|ごみを持ち帰るだけでなく、来たときよりきれいにして帰ることを心がけています。|ごみ を もちかえる だけ で なく きた とき より きれい に して かえる こと を こころがけて います|I try not only to take my trash home but to leave the place cleaner than I found it.
''')

# A transparent kana-to-romaji converter: kana is manually reviewed per item,
# and word boundaries distinguish particles from ordinary syllables.
SINGLE = dict(zip('あいうえお', 'aiueo'))
SINGLE.update({
 'か':'ka','き':'ki','く':'ku','け':'ke','こ':'ko',
 'さ':'sa','し':'shi','す':'su','せ':'se','そ':'so',
 'た':'ta','ち':'chi','つ':'tsu','て':'te','と':'to',
 'な':'na','に':'ni','ぬ':'nu','ね':'ne','の':'no',
 'は':'ha','ひ':'hi','ふ':'fu','へ':'he','ほ':'ho',
 'ま':'ma','み':'mi','む':'mu','め':'me','も':'mo',
 'や':'ya','ゆ':'yu','よ':'yo',
 'ら':'ra','り':'ri','る':'ru','れ':'re','ろ':'ro',
 'わ':'wa','を':'o','ん':'n',
 'が':'ga','ぎ':'gi','ぐ':'gu','げ':'ge','ご':'go',
 'ざ':'za','じ':'ji','ず':'zu','ぜ':'ze','ぞ':'zo',
 'だ':'da','ぢ':'ji','づ':'zu','で':'de','ど':'do',
 'ば':'ba','び':'bi','ぶ':'bu','べ':'be','ぼ':'bo',
 'ぱ':'pa','ぴ':'pi','ぷ':'pu','ぺ':'pe','ぽ':'po',
 'ゔ':'vu',
})
DYNAMIC={}
for a,bas in {'き':'ky','し':'sh','ち':'ch','に':'ny','ひ':'hy','み':'my','り':'ry','ぎ':'gy','じ':'j','び':'by','ぴ':'py','ぢ':'j'}.items():
 for kana,term in zip('ゃゅょ',['a','u','o']):
  DYNAMIC[a+kana]=bas+term
# irregular trigraphs in conventional Hepburn
DYNAMIC.update({'ちぇ':'che','しぇ':'she','じぇ':'je','てぃ':'ti','でぃ':'di','つぁ':'tsa','つぃ':'tsi','つぇ':'tse','つぉ':'tso','しゃ':'sha','しゅ':'shu','しょ':'sho','ちゃ':'cha','ちゅ':'chu','ちょ':'cho','じゃ':'ja','じゅ':'ju','じょ':'jo'})
for c,r in list(SINGLE.items()):
 if r.endswith('i') and len(r)>1 and c not in {'し','ち','じ','ぢ'}:
  for kana,v in zip('ぁぃぅぇぉ','aiueo'): DYNAMIC[c+kana]=r[:-1]+v
for base,head in [('ふ','f'),('て','t'),('で','d'),('と','t'),('ど','d')]:
 for kana,v in zip('ぁぃぅぇぉ','aiueo'):
  DYNAMIC[base+kana]=head+v

def romaji_word(token):
 token=''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in token)
 # An isolated grammatical particle has special pronunciation.
 if token=='は':return 'wa'
 if token=='へ':return 'e'
 if token=='を':return 'o'
 ans='';i=0
 while i<len(token):
  c=token[i]
  if c=='っ':
   nxt=romaji_word(token[i+1:i+3] if token[i+1:i+3] in DYNAMIC else token[i+1:i+2])
   if nxt: ans += 't' if nxt.startswith('ch') else nxt[0]
   i+=1;continue
  if c=='ー':
   previous = next((x for x in reversed(ans) if x in 'aeiou'), '')
   ans+=previous;i+=1;continue
  if c=='ん':
   next_c=token[i+1:i+2]
   if next_c and next_c in 'あいうえおやゆよ':ans+="n'"
   else:ans+='n'
   i+=1;continue
  two=token[i:i+2]
  if two in DYNAMIC: ans+=DYNAMIC[two];i+=2;continue
  if c not in SINGLE:
   raise ValueError(f'Unknown kana {c!r} in reading {token!r}')
  ans+=SINGLE[c];i+=1
 return ans

result=[]
for category, raw in groups:
 seen_levels=Counter()
 for line in raw.splitlines():
  fields=line.strip().split('|')
  if len(fields)!=4:raise ValueError(f'Invalid row: {line}')
  level,jp,segmented,en=fields
  if level not in 'EMH':raise ValueError(line)
  lvl={'E':'easy','M':'medium','H':'hard'}[level]
  seen_levels[lvl]+=1
  # word boundaries are used solely for romaji output, not rendered kana.
  romaji=' '.join(romaji_word(tok) for tok in segmented.split())
  reading=segmented.replace(' ','')
  result.append({'id':f'original-{len(result)+1:03d}',
     'level':lvl,'jp':jp,'reading':reading,'romaji':romaji,
     'english':en,'category':category,'authorship':'original'})
 assert len(seen_levels)==3, (category,seen_levels)
 assert len(raw.splitlines())==15,(category,seen_levels)

# Prevent accidental copying of any full Japanese target already present in
# the previous phrasebook selection (except ubiquitous generic grammar).
old=json.loads((ROOT/'data'/'speaking_phrasebook.json').read_text(encoding='utf-8'))
old_jp={re.sub(r'[\s。、！？!?「」『』・]','',r['jp']) for r in old if r['id'].startswith('essential-')}
new_jp=[re.sub(r'[\s。、！？!?「」『』・]','',r['jp']) for r in result]
assert len(new_jp)==len(set(new_jp)), 'Duplicated new Japanese target'
collisions=[r['jp'] for r in result if re.sub(r'[\s。、！？!?「」『』・]','',r['jp']) in old_jp]
assert not collisions, f'Unexpected exact overlap with previous PDF selection: {collisions}'
assert len(result)>=350
assert len({r['category'] for r in result})>=20
assert all(r['romaji'] and r['reading'] for r in result)
print('Compiled original sentences:',len(result),'categories:',len(groups))
print('Difficulty:',Counter(x['level'] for x in result))

p=ROOT/'data'/'speaking_phrasebook.json'
p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
