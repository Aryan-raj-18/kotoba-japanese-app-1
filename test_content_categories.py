"""Prevent category drift and substring-based classification regressions.

Run using: python test_content_categories.py
"""
import unittest
from app import (categorize, get_emoji, EVERYDAY_WORDS,
                 SPEAKING_PHRASEBOOK, ROADMAP, PICTURE_DICT_WORDS, FREQUENCY_WORDS)


class CategoryTests(unittest.TestCase):
    def test_substring_false_positives(self):
        cases = {
            ('電車', 'train'): 'Transportation',
            ('場所', 'location'): 'Places & Buildings',
            ('多い', 'many'): 'Size & Quantity',
            ('石', 'stone'): 'Nature & Weather',
            ('雪', 'snow'): 'Nature & Weather',
            ('夏休み', 'summer vacation'): 'Seasons & Holidays',
            ('犬', 'dog'): 'Animals',
            ('猫', 'cat'): 'Animals',
            ('牛乳', "(cow's) milk"): 'Food & Drink',
            ('金魚', 'goldfish'): 'Animals',
            ('七夕', 'the Star Festival'): 'Seasons & Holidays',
            ('大学', 'university, college'): 'School & Learning',
            ('高い', 'high, high-priced, tall'): 'Size & Quantity',
            ('魚屋', 'fish market'): 'Places & Buildings',
            ('刺身', 'sliced raw fish'): 'Food & Drink',
        }
        for (word, gloss), expected in cases.items():
            with self.subTest(word=word):
                self.assertEqual(categorize(gloss, word), expected)

    def test_emoji_identity_not_substring(self):
        self.assertNotEqual(get_emoji('train', 'Transportation'), '🌧️')
        self.assertNotEqual(get_emoji('location', 'Places & Buildings'), '🐱')
        self.assertNotEqual(get_emoji('summer vacation', 'Seasons & Holidays'), '🐱')
        self.assertEqual(get_emoji('hot dog', 'Food & Drink'), '🌭')

    def test_everyday_words_have_valid_content_and_categories(self):
        self.assertGreater(len(EVERYDAY_WORDS), 3000)
        for item in EVERYDAY_WORDS:
            self.assertTrue(item.get('word'))
            self.assertTrue(item.get('meaning'))
            self.assertTrue(item.get('category'))

    def test_animal_and_weather_assignments(self):
        by_word = {w['word']: w for w in EVERYDAY_WORDS}
        for word in ('犬', '猫', '鳥', '金魚'):
            self.assertEqual(by_word[word]['category'], 'Animals')
        for word in ('雨', '雪', '風'):
            self.assertEqual(by_word[word]['category'], 'Nature & Weather')
        for word in ('春', '夏', '秋', '冬'):
            self.assertEqual(by_word[word]['category'], 'Seasons & Holidays')
        self.assertEqual(by_word['電車']['category'], 'Transportation')
        self.assertEqual(by_word['場所']['category'], 'Places & Buildings')

    def test_curated_category_mistakes_are_corrected(self):
        picture = {w['word']: w['category'] for w in PICTURE_DICT_WORDS}
        frequency = {w['word']: w['category'] for w in FREQUENCY_WORDS}
        self.assertEqual(picture['動物園'], 'Places & Buildings')
        self.assertEqual(picture['電気自動車'], 'Transportation')
        self.assertEqual(picture['稲妻'], 'Nature & Weather')
        self.assertEqual(frequency['牛乳'], 'Food & Drink')
        self.assertEqual(frequency['アルバイト'], 'Work & Jobs')

    def test_speaking_and_roadmap_data_completeness(self):
        self.assertEqual(len(SPEAKING_PHRASEBOOK), 360)
        self.assertEqual(len({s['id'] for s in SPEAKING_PHRASEBOOK}), len(SPEAKING_PHRASEBOOK))
        self.assertEqual(len({s['category'] for s in SPEAKING_PHRASEBOOK}), 24)
        self.assertGreater(sum(len(sec['chapters']) for sec in ROADMAP), 85)
        for sentence in SPEAKING_PHRASEBOOK:
            self.assertTrue(all(sentence.get(k) for k in ('jp','reading','romaji','english','category','level')))


if __name__ == '__main__':
    unittest.main()
