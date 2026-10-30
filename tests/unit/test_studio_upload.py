# -*- coding: utf-8 -*-
"""Studio upload contract for the drag-and-drop editor."""
from __future__ import absolute_import, division, print_function

import os
import sys
import types
import unittest

import mock
from workbench.runtime import WorkbenchRuntime
from xblock.fields import ScopeIds
from xblock.runtime import DictKeyValueStore, KvsFieldData

import drag_and_drop_v2
from ..utils import TestCaseMixin


EDITOR_JS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'drag_and_drop_v2', 'public', 'js', 'drag_and_drop_edit.js',
)
ASSETS_URL = '/assets/course-v1:org+course+run/'
UPLOADS_URL = '/uploads/course-v1:org+course+run'
COURSE_KEY = 'course-v1:org+course+run'


class _EmptySettings(object):
    """Settings object with no upload-size attribute, so getattr uses its default."""


class StudioUploadContractTests(TestCaseMixin, unittest.TestCase):
    """The editor uploads through CMS handlers without replacing Studio globals."""

    def setUp(self):
        self.block = self._make_block()
        self.patch_workbench()
        self.block.course_id = COURSE_KEY
        self.reverse_calls = []
        self._stub_course_url_reverse()
        self._provide_unicode_builtin()

    @staticmethod
    def _provide_unicode_builtin():
        """xblock-utils load_unicode() calls the Python 2 unicode() builtin."""
        if sys.version_info[0] < 3:
            return
        import builtins

        def unicode_compat(value, encoding='utf-8'):
            if isinstance(value, bytes):
                return value.decode(encoding)
            return value

        builtins.unicode = unicode_compat

    @staticmethod
    def _make_block():
        """Build a block the way the shared helper does, including newer workbench runtimes."""
        runtime = WorkbenchRuntime()
        id_generator = getattr(runtime, 'id_generator', None)
        if id_generator is None:
            from workbench.runtime import ID_MANAGER
            id_generator = ID_MANAGER
        field_data = KvsFieldData(DictKeyValueStore())
        block_type = 'drag_and_drop_v2'
        definition_id = id_generator.create_definition(block_type)
        usage_id = id_generator.create_usage(definition_id)
        scope_ids = ScopeIds('user', block_type, definition_id, usage_id)
        return drag_and_drop_v2.DragAndDropBlock(runtime, field_data, scope_ids=scope_ids)

    def _stub_course_url_reverse(self):
        """CMS is not installed in the xblock test env, so stub its URL helper."""
        urls = {
            'assets_handler': ASSETS_URL,
            'uploads_handler': UPLOADS_URL,
        }

        def reverse_course_url(handler_name, course_key, kwargs=None):
            self.reverse_calls.append((handler_name, course_key, kwargs))
            return urls[handler_name]

        utils_module = types.ModuleType('contentstore.utils')
        utils_module.reverse_course_url = reverse_course_url
        contentstore_module = types.ModuleType('contentstore')
        contentstore_module.utils = utils_module
        patcher = mock.patch.dict(sys.modules, {
            'contentstore': contentstore_module,
            'contentstore.utils': utils_module,
        })
        patcher.start()
        self.addCleanup(patcher.stop)

    def _render_studio_view(self):
        return self.block.studio_view({})

    @staticmethod
    def _js_init_args(fragment):
        if hasattr(fragment, 'json_init_args'):
            return fragment.json_init_args
        return fragment.json_args

    def test_studio_view_passes_cms_upload_urls_and_file_size(self):
        with mock.patch('drag_and_drop_v2.drag_and_drop_v2.settings') as settings_mock:
            settings_mock.MAX_ASSET_UPLOAD_FILE_SIZE_IN_MB = 15
            fragment = self._render_studio_view()
        js_args = self._js_init_args(fragment)

        self.assertEqual(fragment.js_init_fn, 'DragAndDropEditBlock')
        self.assertEqual(js_args['assets_url'], ASSETS_URL)
        self.assertTrue(js_args['assets_url'].endswith('/'))
        self.assertEqual(js_args['uploads_url'], UPLOADS_URL)
        self.assertEqual(js_args['max_file_size_in_mbs'], 15)
        self.assertEqual(self.reverse_calls, [
            ('assets_handler', COURSE_KEY, None),
            ('uploads_handler', COURSE_KEY, None),
        ])
        self.assertNotIn('studioContext', fragment.content)
        self.assertIn('Maximum file size: 15 MB', fragment.content)
        self.assertIn('accept=".jpg,.jpeg,.png,image/png,image/jpeg"', fragment.content)
        self.assertIn('Supported file types: JPG, PNG', fragment.content)

    def test_studio_view_defaults_max_file_size_when_setting_is_missing(self):
        with mock.patch('drag_and_drop_v2.drag_and_drop_v2.settings', _EmptySettings()):
            fragment = self._render_studio_view()

        self.assertEqual(self._js_init_args(fragment)['max_file_size_in_mbs'], 10)
        self.assertIn('Maximum file size: 10 MB', fragment.content)

    def test_studio_submit_persists_custom_background(self):
        background = '/static/custom-background.png'
        response = self.call_handler('studio_submit', {
            'display_name': 'Test Drag & Drop',
            'weight': '1',
            'type_id': 3,
            'custom_background': background,
            'data': {
                'zones': [],
                'items': [],
                'targetImg': background,
                'feedback': {'start': '', 'finish': ''},
            },
        })

        self.assertEqual(response, {'result': 'success'})
        self.assertEqual(self.block.custom_background, background)
        self.assertEqual(self.block.type_id, 3)
        self.assertEqual(self.block.data['targetImg'], background)

    def test_student_view_loads_player_javascript_by_url(self):
        with mock.patch.object(self.block, 'include_theme_files'):
            fragment = self.block.student_view({})
        script_urls = [
            resource.data for resource in fragment.resources
            if resource.kind == 'url' and 'javascript' in resource.mimetype
        ]
        inline_scripts = [
            resource.data for resource in fragment.resources
            if resource.kind == 'text' and 'javascript' in resource.mimetype
        ]

        self.assertIn(
            '/expanded/url/to/drag_and_drop_v2/public/js/vendor/virtual-dom-1.3.0.min.js',
            script_urls,
        )
        self.assertIn(
            '/expanded/url/to/drag_and_drop_v2/public/js/drag_and_drop.js',
            script_urls,
        )
        for source in inline_scripts:
            self.assertNotIn('function DragAndDropBlock', source)

    def test_get_storage_url_quotes_for_python3(self):
        from drag_and_drop_v2.utils import get_storage_url

        with mock.patch('drag_and_drop_v2.utils.staticfiles_storage') as storage:
            storage.url.return_value = '/static/file name.png'
            self.assertEqual(get_storage_url('ignored'), '/static/file%20name.png')
            self.assertEqual(get_storage_url('ignored', raw=True), '/static/file name.png')

    def test_editor_script_uses_server_upload_contract(self):
        with open(EDITOR_JS) as editor_js:
            source = editor_js.read()

        self.assertIn("return params.uploads_url || '';", source)
        self.assertIn("return params.assets_url || '';", source)
        self.assertNotIn('studioContext', source)
        self.assertIn("['jpg', 'jpeg', 'png']", source)
        self.assertIn('maxSizeInMbs * 1000 * 1000', source)
        self.assertIn('asset.size || asset.size === 0 ? asset.size : asset.file_size', source)
        self.assertIn('asset.portable_url || asset.url', source)
        self.assertIn('data-portable-url', source)
        self.assertIn('canvasBackgroundUrl', source)
        self.assertIn("setAttribute('disabled', 'disabled')", source)
        self.assertIn('isDragStillInside', source)
