"""Course sequencing, preserved progress and real review behavior."""
import os, tempfile, sys, unittest
os.environ['KOTOBA_DATA_DIR'] = tempfile.mkdtemp(prefix='kotoba-course-')
if os.environ.get('KOTOBA_TEST_PACKAGE'):
    sys.path.insert(0, os.environ['KOTOBA_TEST_PACKAGE'])
    import kotoba_app.app as K
else:
    import app as K


class RoadmapOrderTests(unittest.TestCase):
    def setUp(self):
        K._save_roadmap_progress(set())
        K._save_roadmap_start('hiragana')
        self.client = K.app.test_client()

    def test_beginner_grammar_and_n5_come_before_n4_n3_n2_n1(self):
        order = K.ROADMAP_CHAPTER_ORDER
        ids = ['hiragana', 'particles-wa-ga-o', 'my-family', 'n5-kanji-checkpoint',
               'computers-internet', 'te-form-basics', 'n3-grammar-01',
               'n2-grammar-01', 'n1-grammar-01', 'grand-review']
        self.assertEqual([order.index(i) for i in ids], sorted(order.index(i) for i in ids))
        self.assertEqual(len(order), 91)
        self.assertEqual(len(set(order)), 91)

    def test_existing_progress_and_start_are_preserved(self):
        done = {'hiragana', 'particles-wa-ga-o', 'te-form-basics', 'n3-grammar-01'}
        K._save_roadmap_progress(done)
        K._save_roadmap_start('n3-grammar-01')
        state = K._roadmap_view_data(None)
        self.assertEqual(state['done'], 4)
        self.assertEqual(state['next_id'], 'n3-grammar-02')
        self.assertEqual(K._load_roadmap_progress(), done)

    def test_completion_advances_through_reordered_chapters(self):
        order = K.ROADMAP_CHAPTER_ORDER
        current = order.index('first-steps-review')
        K._save_roadmap_progress(set(order[:current]))
        result = self.client.post('/api/roadmap/complete', json={'chapter_id':'first-steps-review'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['next_chapter_id'], 'particles-wa-ga-o')

    def test_split_grammar_review_still_covers_both_stages(self):
        scope = K.ROADMAP_CHAPTERS['grammar-foundations-review']['scope']
        self.assertEqual(scope, ['grammar-foundations', 'n4-sentence-building'])
        titles = {r['title'] for r in K._roadmap_summary(None, scope)['rows']}
        self.assertIn(K.ROADMAP_CHAPTERS['particles-wa-ga-o']['title'], titles)
        self.assertIn(K.ROADMAP_CHAPTERS['te-form-basics']['title'], titles)
        self.assertGreater(len(K._build_section_quiz(scope)), 0)
        self.assertEqual(self.client.get('/roadmap/grammar-foundations-review').status_code, 200)

    def test_all_chapters_remain_open(self):
        for chapter_id in K.ROADMAP_CHAPTER_ORDER:
            self.assertEqual(K._roadmap_chapter_status(chapter_id, set()), 'unlocked')
            self.assertIn(self.client.get('/roadmap/' + chapter_id).status_code, (200,302))

    def test_stage_navigation_has_every_section_and_real_n1_content(self):
        html = self.client.get('/roadmap').get_data(as_text=True)
        self.assertIn('Jump to a learning stage', html)
        for section in K.ROADMAP:
            self.assertIn('id="stage-' + section['id'] + '"', html)
        for text in ['N5 · Beginner','N4 · Elementary','N3 · Intermediate','N2 · Advanced','N1 · Advanced']:
            self.assertIn(text, html)
        self.assertNotIn('N2–N1 tools available separately', html)


if __name__ == '__main__': unittest.main()
