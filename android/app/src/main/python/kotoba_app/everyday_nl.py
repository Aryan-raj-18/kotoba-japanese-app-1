"""Original, literal word-learning examples. Never guess contextual readings."""
def build_sentence(word, reading, romaji, meaning, category):
    return {"sentence_kanji":f'「{word}」という言葉を覚えます。',
            "sentence_hiragana":f'「{reading or word}」ということばをおぼえます。',
            "sentence_romaji":f'"{romaji or reading or word}" to iu kotoba o oboemasu.',
            "sentence_en":f'I learn the expression "{meaning}".',
            "usage_note":"Original word-learning example. The English gloss describes this expression; other contexts may use a different sense."}
def build_conv(word, reading, romaji, meaning, category):
    return [{"speaker":"A","kanji":f'「{word}」を読みます。',"hiragana":f'「{reading or word}」をよみます。',"romaji":f'"{romaji or reading or word}" o yomimasu.',"english":f'I read the expression "{meaning}".'},
            {"speaker":"B","kanji":"私も読みます。","hiragana":"わたしもよみます。","romaji":"Watashi mo yomimasu.","english":"I read it too."}]
