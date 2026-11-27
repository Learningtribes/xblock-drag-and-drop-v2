"""Verify HTML is cleaned for learners while author data is preserved."""

import json
import unittest
from copy import deepcopy
from unittest.mock import Mock

from webob import Request
from xblock.fields import ScopeIds
from xblock.runtime import DictKeyValueStore, KvsFieldData, Runtime

from drag_and_drop_v2 import DragAndDropBlock
from drag_and_drop_v2.utils import Constants


class HtmlSanitizationTests(unittest.TestCase):
    def setUp(self):
        super().setUp()
        runtime = Mock(spec=Runtime)
        field_data = KvsFieldData(DictKeyValueStore())
        runtime.service.side_effect = lambda block, name: field_data if name == 'field-data' else None
        runtime.local_resource_url.side_effect = lambda block, path: '/' + path
        self.block = DragAndDropBlock(
            runtime,
            scope_ids=ScopeIds('learner', 'drag-and-drop-v2', 'definition', 'usage'),
        )
        self.author_html = '<article><strong data-note="draft">Réessayez</strong></article>'
        self.learner_html = '<strong>Réessayez</strong>'
        self.zone_title = 'Top & <Bottom>'
        self.data = {
            'zones': [{'uid': 'top', 'title': self.zone_title}],
            'items': [{
                'id': 0,
                'displayName': self.author_html,
                'zones': ['top'],
                'feedback': {'correct': self.author_html, 'incorrect': ''},
            }],
            'feedback': {'start': self.author_html, 'finish': self.author_html},
        }

    def post(self, handler, data):
        request = Request.blank('/', method='POST', body=json.dumps(data).encode('utf-8'))
        response = handler(request)
        self.assertEqual(response.status_code, 200)
        return response.json

    def test_studio_save_keeps_original_html_and_learner_configuration_cleans_it(self):
        result = self.post(self.block.studio_submit, {
            'display_name': self.author_html,
            'problem_text': '<span style="color: red; --draft: blue">Question</span>',
            'data': self.data,
        })
        self.assertEqual(result, {'result': 'success'})

        saved_data = deepcopy(self.block.data)
        config = self.block.get_configuration()
        self.assertEqual(config['title'], self.learner_html)
        self.assertEqual(config['problem_text'], '<span style="color: red;">Question</span>')
        self.assertEqual(config['items'][0]['displayName'], self.learner_html)
        self.assertEqual(config['zones'][0]['title'], self.zone_title)
        self.assertEqual(self.block.display_name, self.author_html)
        self.assertIn('--draft: blue', self.block.question_text)
        self.assertEqual(self.block.data, saved_data)

    def test_legacy_feedback_is_cleaned_in_state_and_on_drop(self):
        self.block.data = self.data
        self.block.mode = Constants.STANDARD_MODE

        state = self.block.get_user_state(Request.blank('/')).json
        self.assertEqual(state['overall_feedback'], [
            {'message': self.learner_html, 'message_class': None},
        ])

        drop = self.post(self.block.drop_item, {'val': 0, 'zone': 'top'})
        self.assertTrue(drop['correct'])
        self.assertEqual(drop['feedback'], state['overall_feedback'])
        self.assertEqual(drop['overall_feedback'], state['overall_feedback'])
        self.assertEqual(self.block.data['items'][0]['feedback']['correct'], self.author_html)

    def test_missing_legacy_answer_label_keeps_the_player_fallback(self):
        del self.data['items'][0]['displayName']
        self.block.data = self.data

        self.assertEqual(self.block.get_configuration()['items'][0]['displayName'], '')
        self.assertNotIn('displayName', self.block.data['items'][0])
