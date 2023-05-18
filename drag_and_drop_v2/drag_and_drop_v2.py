# -*- coding: utf-8 -*-
""" Drag and Drop v2 XBlock """


import copy
import json
import logging
import urllib
import webob

from pipeline_mako.helpers.studiofrontend import load_sfe_i18n_messages

from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Scope, String, Dict, Float, Boolean, Integer, List
from xblock.fragment import Fragment
from xblock.scorable import ScorableXBlockMixin, Score
from xblockutils.resources import ResourceLoader
from xblockutils.settings import XBlockWithSettingsMixin, ThemableXBlockMixin
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import AssetKey, CourseKey

from .utils import (
    _, DummyTranslationService, FeedbackMessage, FeedbackMessages,
    ItemStats, StateMigration, Constants, get_storage_url,
    make_state_from_attempt, get_max_items_per_zone, present_feedback
)
from .default_data import DEFAULT_EMPTY_DATA
from .tabs_header import TabsHeader
from .zone_template import TriangleTemplate, ZonesDefinition, ZONE_TPL_DEFINITIONS


loader = ResourceLoader(__name__)
logger = logging.getLogger(__name__)


@XBlock.wants('settings')
@XBlock.needs('i18n')
class DragAndDropBlock(
    ScorableXBlockMixin,
    XBlock,
    XBlockWithSettingsMixin,
    ThemableXBlockMixin
):
    """XBlock that implements a friendly Drag-and-Drop problem
    """
    SOLUTION_CORRECT = 'correct'
    SOLUTION_PARTIAL = 'partial'
    SOLUTION_INCORRECT = 'incorrect'

    GRADE_FEEDBACK_CLASSES = {
        SOLUTION_CORRECT: FeedbackMessages.MessageClasses.CORRECT_SOLUTION,
        SOLUTION_PARTIAL: FeedbackMessages.MessageClasses.PARTIAL_SOLUTION,
        SOLUTION_INCORRECT: FeedbackMessages.MessageClasses.INCORRECT_SOLUTION,
    }

    PROBLEM_FEEDBACK_CLASSES = {
        SOLUTION_CORRECT: FeedbackMessages.MessageClasses.CORRECT_SOLUTION,
        SOLUTION_PARTIAL: None,
        SOLUTION_INCORRECT: None
    }

    display_name = String(
        display_name=_('Title'),
        help=_('The title of the drag and drop problem. The title is displayed to learners.'),
        scope=Scope.settings,
        default=_('Drag & Drop'),
        enforce_type=True,
    )
    # Keep it for being compatible with old version only ( In new version, we always set it with `ASSESSMENT_MODE` )
    mode = String(
        display_name=_('Mode'),
        help=_(
            'Standard mode: the problem provides immediate feedback each time '
            'a learner drops an item on a target zone. '
            'Assessment mode: the problem provides feedback only after '
            'a learner drops all available items on target zones.'
        ),
        scope=Scope.settings,
        values=[
            {'display_name': _('Standard'), 'value': Constants.STANDARD_MODE},
            {'display_name': _('Assessment'), 'value': Constants.ASSESSMENT_MODE},
        ],
        default=Constants.ASSESSMENT_MODE,  # Assign with `assessment mode` instead of `standard mode` in new version
        enforce_type=True,
    )
    # In new version, the value is `None` always.
    max_attempts = Integer(
        display_name=_('Maximum attempts'),
        help=_(
            'Defines the number of times a student can try to answer this problem. '
            'If the value is not set, infinite attempts are allowed.'
        ),
        scope=Scope.settings,
        default=None,
        enforce_type=True,
    )

    show_title = Boolean(
        display_name=_('Show title'),
        help=_('Display the title to the learner?'),
        scope=Scope.settings,
        default=True,                       # Always activated this field in new version
        enforce_type=True,
    )

    question_text = String(
        display_name=_('Problem text'),
        help=_('The description of the problem or instructions shown to the learner.'),
        scope=Scope.settings,
        default='',
        enforce_type=True,
    )

    show_question_header = Boolean(
        display_name=_('Show "Problem" heading'),
        help=_('Display the heading "Problem" above the problem text?'),
        scope=Scope.settings,
        default=True,
        enforce_type=True,
    )

    weight = Float(
        display_name=_('Problem Weight'),
        help=_('Defines the number of points the problem is worth.'),
        scope=Scope.settings,
        default=1,
        enforce_type=True,
    )

    item_background_color = String(
        display_name=_('Item background color'),
        help=_('The background color of draggable items in the problem (example: \'blue\' or \'#0000ff\').'),
        scope=Scope.settings,
        default='',
        enforce_type=True,
    )

    item_text_color = String(
        display_name=_('Item text color'),
        help=_('Text color to use for draggable items (example: \'white\' or \'#ffffff\').'),
        scope=Scope.settings,
        default="",
        enforce_type=True,
    )
    # In new version, the value is `None` always.
    max_items_per_zone = Integer(
        display_name=_('Maximum items per zone'),
        help=_('This setting limits the number of items that can be dropped into a single zone.'),
        scope=Scope.settings,
        default=None,
        enforce_type=True,
    )

    data = Dict(
        display_name=_('Problem data'),
        help=_(
            'Information about zones, items, feedback, and background image for this problem. '
            'This information is derived from the input that a course author provides via the interactive editor '
            'when configuring the problem.'
        ),
        scope=Scope.content,
        default=DEFAULT_EMPTY_DATA,
        enforce_type=True,
    )

    item_state = Dict(
        help=_('Information about current positions of items that a learner has dropped on the target image.'),
        scope=Scope.user_state,
        default={},
        enforce_type=True,
    )

    attempts = Integer(
        help=_('Number of attempts learner used'),
        scope=Scope.user_state,
        default=0,
        enforce_type=True,
    )

    completed = Boolean(
        help=_('Indicates whether a learner has completed the problem at least once'),
        scope=Scope.user_state,
        default=False,
        enforce_type=True,
    )

    grade = Float(
        help=_('DEPRECATED. Keeps maximum score achieved by student as a weighted value.'),
        scope=Scope.user_state,
        default=0
    )

    raw_earned = Float(
        help=_('Keeps maximum score achieved by student as a raw value between 0 and 1.'),
        scope=Scope.user_state,
        default=0,
        enforce_type=True,
    )

    type_id = Integer(
        help=_('Background index of pyramid, rectangles, blank, custom'),
        scope=Scope.settings,
        default=None,
        enforce_type=True,
    )

    custom_background = String(
        help=_('Background image of custom'),
        scope=Scope.settings,
        default=None,
        enforce_type=True,
    )

    block_settings_key = 'drag-and-drop-v2'

    @property
    def definition_data(self):
        """Return instance of class ZonesDefinition(self._tpl_data)
        """
        if hasattr(self, 'user_definition_data'):
            return self.user_definition_data

        _user_definition_data = ZonesDefinition(self.data)
        setattr(self, 'user_definition_data', _user_definition_data)

        return self.user_definition_data

    def max_score(self):
        """Return the problem's max score, which for DnDv2 always equals 1.
            Required by the grading system in the LMS.
        """
        return 1

    def get_score(self):
        """Return the problem's current score as raw values.
        """
        if self._get_raw_earned_if_set() is None:
            self.raw_earned = self._learner_raw_score()
        return Score(self.raw_earned, self.max_score())

    def set_score(self, score):
        """Sets the score on this block.
            Takes a Score namedtuple containing a raw
            score and possible max (for this block, we expect that this will
            always be 1).
        """
        assert score.raw_possible == self.max_score()
        self.raw_earned = score.raw_earned

    def calculate_score(self):
        """Returns a newly-calculated raw score on the problem for the learner
            based on the learner's current state.
        """
        return Score(self._learner_raw_score(), self.max_score())

    def has_submitted_answer(self):
        """Returns True if the user has made a submission.
        """
        return self.fields['raw_earned'].is_set_on(self) or self.fields['grade'].is_set_on(self)

    def weighted_grade(self):
        """Returns the block's current saved grade multiplied by the block's
            weight- the number of points earned by the learner.
        """
        return self.raw_earned * self.weight

    def _learner_raw_score(self):
        """Calculate raw score for learner submission.

            As it is calculated as ratio of correctly placed (or left in bank in case of decoys) items to
            total number of items, it lays in interval [0..1]
        """
        correct_count, total_count = self._get_items_correctness_stats()
        return correct_count / float(total_count)

    @XBlock.supports("multi_device")  # Enable this block for use in the mobile app via webview
    def student_view(self, context):
        """
        Player view, displayed to the student
        """

        fragment = Fragment()
        fragment.add_content(loader.render_django_template('/templates/html/drag_and_drop.html',
                                                           i18n_service=self.i18n_service))
        css_urls = (
            'public/css/drag_and_drop.css',
        )
        js_urls = (
            'public/js/vendor/virtual-dom-1.3.0.min.js',
            'public/js/drag_and_drop.js',
        )
        for css_url in css_urls:
            fragment.add_css_url(self.runtime.local_resource_url(self, css_url))
        for js_url in js_urls:
            fragment.add_javascript_url(self.runtime.local_resource_url(self, js_url))

        self.include_theme_files(fragment)

        fragment.initialize_js('DragAndDropBlock', self.get_configuration())

        return fragment

    def get_configuration(self):
        """Get the configuration data for the student_view.
            The configuration is all the settings defined by the author, except for correct answers
            and feedback.
        """
        def items_without_answers():
            """Removes feedback and answer from items
            """
            items = copy.deepcopy(self.data.get('items', []))
            for item in items:
                del item['feedback']
                # Use item.pop to remove both `item['zone']` and `item['zones']`; we don't have
                # a guarantee that either will be present, so we can't use `del`. Legacy instances
                # will have `item['zone']`, while current versions will have `item['zones']`.
                item.pop('zone', None)
                item.pop('zones', None)
                # Fall back on "backgroundImage" to be backward-compatible.
                image_url = item.get('imageURL') or item.get('backgroundImage')
                if image_url:
                    item['expandedImageURL'] = self._expand_static_url(image_url)
                else:
                    item['expandedImageURL'] = ''
            return items

        return {
            "mode": self.mode,
            "zones": self.definition_data.get_compatible_zones(),
            "max_attempts": self.max_attempts,
            "graded": getattr(self, 'graded', False),
            "weighted_max_score": self.max_score() * self.weight,
            "max_items_per_zone": self.max_items_per_zone,
            # SDK doesn't supply url_name.
            "url_name": getattr(self, 'url_name', ''),
            "display_zone_labels": self.data.get('displayLabels', False),
            "display_zone_borders": self.data.get('displayBorders', False),
            "items": items_without_answers(),
            "title": self.display_name,
            "show_title": self.show_title,
            "problem_text": self.question_text,
            "show_problem_header": self.show_question_header,
            "target_img_expanded_url": self.target_img_expanded_url,
            "target_img_description": '',
            "item_background_color": self.item_background_color or None,
            "item_text_color": self.item_text_color or None,
            # final feedback (data.feedback.finish) is not included - it may give away answers.
        }

    def studio_view(self, context):
        """Editing view in Studio
        """
        # Get an 'id_suffix' string that is unique for this block.
        # We append it to HTML element ID attributes to ensure multiple instances of the DnDv2 block
        # on the same page don't share the same ID value.
        # We avoid using ID attributes in preference to classes, but sometimes we still need IDs to
        # connect 'for' and 'aria-describedby' attributes to the associated elements.
        def _get_block_id(xblock):
            """Return unique ID of this block. Useful for HTML ID attributes.
                Works both in LMS/Studio and workbench runtimes:
                - In LMS/Studio, use the location.html_id method.
                - In the workbench, use the usage_id.
            """
            return xblock.location.html_id() if hasattr(xblock, 'location') else unicode(xblock.scope_ids.usage_id)

        course_module = modulestore().get_course(self.course_id)

        context = {
            'course_id': "{}".format(self.course_id),
            'course': {
                'lang': course_module.language,
                'org': self.course_id.org,
                'number': self.course_id.course,
                'run': self.course_id.run,
                'url_name': course_module.url_name,
                'display_name': course_module.display_name
            },
            'predefined_tabs': TabsHeader(),
            'id_suffix': _get_block_id(self),
            'fields': self.fields,
            'self': self,
            'data': urllib.quote(json.dumps(self.data)),
            'type_id': self.type_id,
            'tpl_summaries': ZONE_TPL_DEFINITIONS.get_templates_summary(self, self.runtime.local_resource_url),
            ### For editImageModal rendering
            'common_min_css': get_storage_url('/common/js/vendor/learningtribes-studio-frontend/dist/common.min.css'),
            'assets_min_css': get_storage_url('/common/js/vendor/learningtribes-studio-frontend/dist/assets.min.css'),
            'runtime_min_js': get_storage_url('common/js/vendor/learningtribes-studio-frontend/dist/runtime.min.js'),
            'common_min_js': get_storage_url('common/js/vendor/learningtribes-studio-frontend/dist/common.min.js'),
            'assets_min_js': get_storage_url('common/js/vendor/learningtribes-studio-frontend/dist/assets.min.js'),
            'default_finish_feedback': ZonesDefinition.FINISH_FEEDBACK
        }

        fragment = Fragment()
        fragment.add_content(
            loader.render_django_template(
                '/templates/html/drag_and_drop_edit_v3.html',
                context=context, i18n_service=self.i18n_service
            )
        )
        css_urls = (
            'public/css/drag_and_drop_edit.css',
        )
        js_urls = (
            'public/js/vendor/handlebars-v1.1.2.js',
            'public/js/drag_and_drop_edit.js'
        )
        for css_url in css_urls:
            fragment.add_css_url(self.runtime.local_resource_url(self, css_url))

        for js_url in js_urls:
            fragment.add_javascript_url(self.runtime.local_resource_url(self, js_url))

        # Do a bit of manipulation so we get the appearance of a list of zone options on
        # items that still have just a single zone stored
        items = self.data.get('items', [])

        for item in items:
            zones = self.definition_data.get_zones_by_item_id(item['id'])
            # Note that we appear to be mutating the state of the XBlock here, but because
            # the change won't be committed, we're actually just affecting the data that
            # we're going to send to the client, not what's saved in the backing store.
            item['zones'] = zones
            item.pop('zone', None)

        fragment.initialize_js('DragAndDropEditBlock', {
            'data': self.data,
            'type_id': self.type_id,
            'custom_background': self.custom_background,
            'tpl_summaries': ZONE_TPL_DEFINITIONS.get_templates_summary(self, self.runtime.local_resource_url),
            'predefined_templates': ZONE_TPL_DEFINITIONS.predefined_templates,
            'target_img_expanded_url': self.target_img_expanded_url,
            'pyramid_background_image_url': self.pyramid_background_image_url,
        })

        return fragment

    @XBlock.json_handler
    def background_check(self, request_data, suffix=''):
        def _get_block_id(xblock):
            """Return unique ID of this block. Useful for HTML ID attributes.
                Works both in LMS/Studio and workbench runtimes:
                - In LMS/Studio, use the location.html_id method.
                - In the workbench, use the usage_id.
            """
            return xblock.location.html_id() if hasattr(xblock, 'location') else unicode(xblock.scope_ids.usage_id)

        xblock_id = _get_block_id(self)
        xblocks = modulestore().get_items(self.course_id, qualifiers={'category': 'drag-and-drop-v2'})

        asset_id = request_data['asset_id']

        for xblock in xblocks:
            other_xblock_id = _get_block_id(xblock)
            data = getattr(xblock, 'data', '')
            # other_xblock_asset_id = data['targetImg'] if 'targetImg' in data else None
            other_xblock_asset_id = getattr(xblock, 'custom_background', '')

            if other_xblock_id != xblock_id:
                if other_xblock_asset_id and other_xblock_asset_id[1:] == asset_id:
                    return {
                        'result': 'success',
                    }

        course_key = CourseKey.from_string('{}'.format(self.course_id))
        asset_key = AssetKey.from_string(asset_id) if asset_id else None

        try:
            from contentstore.views.assets import delete_asset
            delete_asset(course_key, asset_key)
            logging.info('Deleted unused asset: {file_name}, asset_key: {asset_key}, '
                         'course_id: {course_id}'.format(file_name=asset_key.name,
                                                         asset_key=asset_key,
                                                         course_id=course_key))
            return {
                'result': 'success',
            }
        except Exception as e:
            return {
                'result': 'background_check to delete: ' + str(e),
            }

    @XBlock.json_handler
    def studio_submit(self, submissions, suffix=''):
        """Handles studio save.
        """
        def _validate_zone_uids(zones_items_data):
            if zones_items_data:
                # Raise error if duplicated Zone UIDs exist in parameters of HTTP POST.
                zones_uids = [zone['uid'] for zone in zones_items_data.get('zones', [])]
                zones_uids_set = set(zones_uids)
                if len(zones_uids) != len(zones_uids_set):
                    return {
                        'result': 'error',
                        'messages': ['Duplicated zone uid in POST arguments']
                    }
                # Raise error if illegal zone uid related with items.
                items_used_zones = {zone_uid for item in zones_items_data.get('items', []) for zone_uid in item['zones']}
                if items_used_zones - zones_uids_set:
                    return {
                        'result': 'error',
                        'messages': ['Illegal zone uid in item objects']
                    }

            return None

        zones_items_data = submissions.get('data')
        json_error_resp = _validate_zone_uids(zones_items_data)
        if json_error_resp:
            return json_error_resp

        if 'display_name' in submissions:
            self.display_name = submissions['display_name']
        # Only support `assessment mode` in new version
        # But still keep field `mode` and value `Constants.STANDARD_MODE` loaded from DB to be compatible with old version
        if 'mode' in submissions:
            self.mode = Constants.ASSESSMENT_MODE
        # In new version : Infinite attempts are allowed. and keep the field `max_attempts` to be compatible with old version
        if 'max_attempts' in submissions:
            self.max_attempts = None
        if 'show_title' in submissions:
            self.show_title = submissions['show_title']
        if 'problem_text' in submissions:
            self.question_text = submissions['problem_text']
        if 'show_problem_header' in submissions:
            self.show_question_header = submissions['show_problem_header']
        if 'weight' in submissions:
            self.weight = float(submissions['weight'])
        if 'item_background_color' in submissions:
            self.item_background_color = submissions['item_background_color']
        if 'item_text_color' in submissions:
            self.item_text_color = submissions['item_text_color']
        # In new version we remove this limitation
        if 'max_items_per_zone' in submissions:
            self.max_items_per_zone = None
        if zones_items_data:
            self.data = zones_items_data
        if 'feedback' in submissions:
            feedback = submissions['feedback']
            if 'start' in feedback:
                self.data['feedback']['start'] = feedback['start']
            if 'finish' in feedback:
                self.data['feedback']['finish'] = feedback['finish']
        if 'type_id' in submissions:
            self.type_id = submissions['type_id']
        if 'custom_background' in submissions:
            self.custom_background = submissions['custom_background']

        return {
            'result': 'success',
        }

    @XBlock.json_handler
    def drop_item(self, item_attempt, suffix=''):
        """Handles dropping item into a zone.
        """
        if self.mode != Constants.ASSESSMENT_MODE:
            if not self.definition_data.get_zone_info_by_uid(item_attempt['zone']):
                raise JsonHandlerError(400, 'Item zone data is invalid.')

        if self.mode == Constants.ASSESSMENT_MODE:
            return self._drop_item_assessment(item_attempt)
        elif self.mode == Constants.STANDARD_MODE:
            return self._drop_item_standard(item_attempt)
        else:
            raise JsonHandlerError(
                500,
                self.i18n_service.gettext('Unknown DnDv2 mode {mode} - course is misconfigured').format(self.mode)
            )

    def _drop_item_standard(self, item_attempt):
        """Handles dropping item to a zone in standard mode.
        """
        _item = self.definition_data.get_item_by_id(item_attempt['val'])
        is_correct = self.definition_data.is_attempt_correct(
            item_attempt, self.mode == Constants.ASSESSMENT_MODE
        )  # Student placed item in a correct zone
        if is_correct:  # In standard mode state is only updated when attempt is correct
            self.item_state[str(_item['id'])] = make_state_from_attempt(item_attempt, is_correct)

        self._mark_complete_and_publish_grade()  # must happen before _get_feedback
        self._publish_item_dropped_event(item_attempt, is_correct)

        item_feedback_key = 'correct' if is_correct else 'incorrect'
        item_feedback = FeedbackMessage(_item['feedback'][item_feedback_key], None)
        overall_feedback, __ = self._get_feedback()
        return {
            'correct': is_correct,
            'grade': self._get_weighted_earned_if_set(),
            'finished': self._are_all_answers_correct(),
            'overall_feedback': present_feedback(overall_feedback),
            'feedback': present_feedback([item_feedback])
        }

    def _drop_item_assessment(self, item_attempt):
        """Handles dropping item into a zone in assessment mode
        """
        if not self.attempts_remain:
            raise JsonHandlerError(409, self.i18n_service.gettext("Max number of attempts reached"))

        _item = self.definition_data.get_item_by_id(item_attempt['val'])
        is_correct = self.definition_data.is_attempt_correct(
            item_attempt, self.mode == Constants.ASSESSMENT_MODE
        )
        if item_attempt['zone'] is None:
            self.item_state.pop(str(_item['id']), None)
            self._publish_item_to_bank_event(_item['id'], is_correct)
        else:
            # State is always updated in assessment mode to store intermediate item positions
            # Key : item_id ==> Value : {'zone': 'zone_123_id', 'correct': True/False}
            self.item_state[str(_item['id'])] = make_state_from_attempt(item_attempt, is_correct)
            self._publish_item_dropped_event(item_attempt, is_correct)

        return {}

    @XBlock.json_handler
    def do_attempt(self, data, suffix=''):
        """Checks submitted solution and returns feedback.

            Raises:
                 * JsonHandlerError with 400 error code in standard mode.
                 * JsonHandlerError with 409 error code if no more attempts left
        """
        # Validates if `do_attempt` handler should be executed
        if self.mode != Constants.ASSESSMENT_MODE:
            raise JsonHandlerError(400, self.i18n_service.gettext("do_attempt handler should only be called for assessment mode"))
        if not self.attempts_remain:
            raise JsonHandlerError(409, self.i18n_service.gettext("Max number of attempts reached"))

        self.attempts += 1
        # These implicit dependencies between methods exist because most of them use `item_state` or other
        # fields, either as an "input" (i.e. read value) or as output (i.e. set value) or both. As a result,
        # incorrect order of invocation causes issues:
        self._mark_complete_and_publish_grade()  # must happen before _get_feedback - sets grade

        correct = self._are_all_answers_correct()  # must happen before manipulating item_state - reads item_state
        overall_feedback_msgs, misplaced_ids = self._get_feedback(include_item_feedback=True)

        misplaced_items = []
        for item_id in misplaced_ids:
            # Don't delete misplaced item states on the final attempt.
            if self.attempts_remain:
                del self.item_state[item_id]
            misplaced_items.append(self.definition_data.get_item_by_id(int(item_id)))

        feedback_msgs = [FeedbackMessage(item['feedback']['incorrect'], None) for item in misplaced_items]
        return {
            'correct': correct,
            'attempts': self.attempts,
            'grade': self._get_weighted_earned_if_set(),
            'misplaced_items': list(misplaced_ids),
            'feedback': present_feedback(feedback_msgs),
            'overall_feedback': present_feedback(overall_feedback_msgs)
        }

    def _mark_complete_and_publish_grade(self):
        """Helper method to update `self.completed` and submit grade event if appropriate conditions met.
        """
        # This method implicitly depends on self.item_state (via _are_all_answers_correct and _learner_raw_score)
        # and also updates self.raw_earned if some conditions are met. As a result this method implies some order of
        # invocation:
        # * it should be called after learner-caused updates to self.item_state is applied
        # * it should be called before self.item_state cleanup is applied (i.e. returning misplaced items to item bank)
        # * it should be called before any method that depends on self.raw_earned (i.e. self._get_feedback)

        # Splitting it into a "clean" functions will allow to capture this implicit invocation order in caller method
        # and help avoid bugs caused by invocation order violation in future.

        # There's no going back from "completed" status to "incomplete"
        self.completed = self.completed or self._are_all_answers_correct() or not self.attempts_remain
        current_raw_earned = self._learner_raw_score()
        # ... and from higher grade to lower
        # if we have an old-style (i.e. unreliable) grade, override no matter what
        saved_raw_earned = self._get_raw_earned_if_set()
        if current_raw_earned is None or current_raw_earned > saved_raw_earned:
            self.raw_earned = current_raw_earned
            self._publish_grade(Score(self.raw_earned, self.max_score()))

        # and no matter what - emit progress event for current user
        self.runtime.publish(self, "progress", {})

    def _publish_item_dropped_event(self, attempt, is_correct):
        """Publishes item dropped event.
        """
        item = self.definition_data.get_item_by_id(attempt['val'])
        # attempt should already be validated here - not doing the check for existing zone again
        zone = self.definition_data.get_zone_info_by_uid(attempt['zone'])

        item_label = item.get("displayName")
        if not item_label:
            item_label = item.get("imageURL")

        self.runtime.publish(self, 'edx.drag_and_drop_v2.item.dropped', {
            'item': item_label,
            'item_id': item['id'],
            'location': zone.get("title"),
            'location_id': zone.get("uid"),
            'is_correct': is_correct,
        })

    def _publish_item_to_bank_event(self, item_id, is_correct):
        """Publishes event when item moved back to the bank in assessment mode.
        """
        item = self.definition_data.get_item_by_id(item_id)

        item_label = item.get("displayName")
        if not item_label:
            item_label = item.get("imageURL")

        self.runtime.publish(self, 'edx.drag_and_drop_v2.item.dropped', {
            'item': item_label,
            'item_id': item['id'],
            'location': 'item bank',
            'location_id': -1,
            'is_correct': is_correct,
        })

    @XBlock.json_handler
    def publish_event(self, data, suffix=''):
        """Handler to publish XBlock event from frontend
        """
        try:
            event_type = data.pop('event_type')
        except KeyError:
            return {'result': 'error', 'message': 'Missing event_type in JSON data'}

        self.runtime.publish(self, event_type, data)
        return {'result': 'success'}

    @XBlock.json_handler
    def reset(self, data, suffix=''):
        """Resets problem to initial state
        """
        self.item_state = {}
        return self._get_user_testing_state()

    @XBlock.json_handler
    def show_answer(self, data, suffix=''):
        """Returns correct answer in assessment mode.

            Raises:
                 * JsonHandlerError with 400 error code in standard mode.
                 * JsonHandlerError with 409 error code if there are still attempts left
        """
        if self.mode != Constants.ASSESSMENT_MODE:
            raise JsonHandlerError(400, self.i18n_service.gettext("show_answer handler should only be called for assessment mode"))
        if self.attempts_remain:
            raise JsonHandlerError(409, self.i18n_service.gettext("There are attempts remaining"))

        return self.definition_data.get_correct_state()

    @XBlock.json_handler
    def expand_static_url(self, url, suffix=''):
        """ AJAX-accessible handler for expanding URLs to static [image] files """
        return {'url': self._expand_static_url(url)}

    @property
    def i18n_service(self):
        """ Obtains translation service """
        i18n_service = self.runtime.service(self, "i18n")
        return i18n_service if i18n_service else DummyTranslationService()

    @property
    def target_img_expanded_url(self):
        """Get the expanded URL to the target image (the image items are dragged onto).
        """
        if self.data.get('targetImg'):
            return self._expand_static_url(self.data['targetImg'])
        elif self.type_id == TriangleTemplate.TYPE_ID:
            return self.pyramid_background_image_url
        elif self.type_id in ZONE_TPL_DEFINITIONS.ALL_SUPPORTED_TEMPLATES:
            return ''

    @property
    def pyramid_background_image_url(self):
        """The URL to the `pyramid` background image, shown when pyramid template is selected
        """
        return self.runtime.local_resource_url(self, "public/img/triangle.png")

    @property
    def attempts_remain(self):
        """Checks if current student still have more attempts.
        """
        return self.max_attempts is None or self.max_attempts == 0 or self.attempts < self.max_attempts

    @XBlock.handler
    def get_user_state(self, request, suffix=''):
        """ GET all user-specific data, and any applicable feedback """
        return webob.Response(
            body=json.dumps(self._get_user_testing_state()),
            content_type='application/json'
        )

    def _get_feedback(self, include_item_feedback=False):
        """Builds overall feedback for both standard and assessment modes
        """
        _answer_correctness = self.answers_correctness

        if self.mode == Constants.STANDARD_MODE or not self.attempts:
            feedback_key = 'finish' if _answer_correctness == self.SOLUTION_CORRECT else 'start'
            return [FeedbackMessage(self.data['feedback'][feedback_key], None)], set()

        items = self._get_classified_stats_of_user_items()
        missing_ids = items.required - items.placed
        misplaced_ids = items.placed - items.correctly_placed
        feedback_msgs = []

        def _add_msg_if_exists(ids_list, message_template, message_class):
            """ Adds message to feedback messages if corresponding items list is not empty """
            if ids_list:
                message = message_template(len(ids_list), self.i18n_service.ngettext)
                feedback_msgs.append(FeedbackMessage(message, message_class))

        if self.item_state or include_item_feedback:
            _add_msg_if_exists(
                items.correctly_placed,
                FeedbackMessages.correctly_placed,
                FeedbackMessages.MessageClasses.CORRECTLY_PLACED
            )

            # Misplaced items are not returned to the bank on the final attempt.
            if self.attempts_remain:
                misplaced_template = FeedbackMessages.misplaced_returned
            else:
                misplaced_template = FeedbackMessages.misplaced

            _add_msg_if_exists(misplaced_ids, misplaced_template, FeedbackMessages.MessageClasses.MISPLACED)
            _add_msg_if_exists(missing_ids, FeedbackMessages.not_placed, FeedbackMessages.MessageClasses.NOT_PLACED)

        if self.attempts_remain and (misplaced_ids or missing_ids):
            problem_feedback_message = self.data['feedback']['start']
        else:
            problem_feedback_message = self.data['feedback']['finish']

        problem_feedback_class = self.PROBLEM_FEEDBACK_CLASSES.get(_answer_correctness, None)
        grade_feedback_class = self.GRADE_FEEDBACK_CLASSES.get(_answer_correctness, None)

        feedback_msgs.append(FeedbackMessage(problem_feedback_message, problem_feedback_class))

        if self.weight > 0:
            if self.attempts_remain:
                grade_feedback_template = FeedbackMessages.GRADE_FEEDBACK_TPL
            else:
                grade_feedback_template = FeedbackMessages.FINAL_ATTEMPT_TPL

            feedback_msgs.append(
                FeedbackMessage(grade_feedback_template.format(score=self.weighted_grade()), grade_feedback_class)
            )

        return feedback_msgs, misplaced_ids

    def _expand_static_url(self, url):
        """This is required to make URLs like '/static/dnd-test-image.png' work (note: that is the
            only portable URL format for static files that works across export/import and reruns).
            This method is unfortunately a bit hackish since XBlock does not provide a low-level API
            for this.
        """
        if hasattr(self.runtime, 'replace_urls'):
            url = self.runtime.replace_urls(u'"{}"'.format(url))[1:-1]
        elif hasattr(self.runtime, 'course_id'):
            # edX Studio uses a different runtime for 'studio_view' than 'student_view',
            # and the 'studio_view' runtime doesn't provide the replace_urls API.
            try:
                from static_replace import replace_static_urls  # pylint: disable=import-error
                url = replace_static_urls(u'"{}"'.format(url), None, course_id=self.runtime.course_id)[1:-1]
            except ImportError:
                pass
        return url

    def _get_user_dropped_items_state(self):
        """Returns a copy of the user item state.
            Converts to a dict if data is stored in legacy tuple form.

            @return:            user dropped items' state
                                    ==>  Sample: {item_id, ['zone' : 'zone_123_id',  'correct': True/False]}
            @rtype:             dict
        """
        # IMPORTANT: this method should always return a COPY of self.item_state - it is called from get_user_state
        # handler and the data it returns is manipulated there to hide correctness of items placed.
        migrator = StateMigration(self)

        return {
            item_id: migrator.apply_item_state_migrations(item_id, item)
            for item_id, item in self.item_state.items()
        }

    def _get_user_testing_state(self):
        """ Get all user-specific data, and any applicable feedback """
        _user_dropped_items_state = self._get_user_dropped_items_state()
        # In assessment mode, we do not want to leak the correctness info for individual items to the frontend,
        # so we remove "correct" from all items when in assessment mode.
        if self.mode == Constants.ASSESSMENT_MODE:
            for item in _user_dropped_items_state.values():
                del item["correct"]

        overall_feedback_msgs, __ = self._get_feedback()

        return {
            'items': _user_dropped_items_state,
            'finished': self._are_all_answers_correct() if self.mode == Constants.STANDARD_MODE else not self.attempts_remain,
            'attempts': self.attempts,
            'grade': self._get_weighted_earned_if_set(),
            'overall_feedback': present_feedback(overall_feedback_msgs)
        }

    def _get_classified_stats_of_user_items(self):
        """Returns a named tuple containing required, decoy, placed, correctly
            placed, and correctly unplaced decoy items.

            Returns:
                namedtuple: (required, placed, correctly_placed, decoy, decoy_in_bank)
                    * required - IDs of items that must be placed on the board
                    * placed - IDs of items actually placed on the board
                    * correctly_placed - IDs of items that were placed correctly
                    * decoy - IDs of decoy items
                    * decoy_in_bank - IDs of decoy items that were unplaced
        """
        _user_dropped_items_state = self._get_user_dropped_items_state()
        _all_items_ids = self.definition_data.get_valid_item_ids()

        required = set(item_id for item_id in _all_items_ids if self.definition_data.get_zones_by_item_id(int(item_id)))
        placed = set(item_id for item_id in _all_items_ids if item_id in _user_dropped_items_state)
        correctly_placed = set(item_id for item_id in placed if _user_dropped_items_state[item_id]['correct'])
        decoy = _all_items_ids - required
        decoy_in_bank = set(item_id for item_id in decoy if item_id not in _user_dropped_items_state)

        return ItemStats(required, placed, correctly_placed, decoy, decoy_in_bank)

    def _get_items_correctness_stats(self):
        """Returns a tuple representing the number of correctly placed items,
            and the total number of items required (including decoy items).
        """
        _items_stats = self._get_classified_stats_of_user_items()

        correct_count = len(_items_stats.correctly_placed) + len(_items_stats.decoy_in_bank)
        total_count = len(_items_stats.required) + len(_items_stats.decoy)

        return correct_count, total_count

    def _get_raw_earned_if_set(self):
        """Returns student's grade if already explicitly set, otherwise returns None.
            This is different from self.raw_earned which returns 0 by default.
        """
        return self.raw_earned if self.fields['raw_earned'].is_set_on(self) else None

    def _get_weighted_earned_if_set(self):
        """Returns student's grade with the problem weight applied if set, otherwise None.
        """
        return self.weighted_grade() if self.fields['raw_earned'].is_set_on(self) else None

    @property
    def answers_correctness(self):
        """Return answers correctness:

            Returns:
                string: Correct/Incorrect/Partial
                    * Correct: All items are at their correct place.
                    * Partial: Some items are at their correct place.
                    * Incorrect: None items are at their correct place.
        """
        correct_count, total_count = self._get_items_correctness_stats()
        if correct_count == total_count:
            return self.SOLUTION_CORRECT
        elif correct_count == 0:
            return self.SOLUTION_INCORRECT
        else:
            return self.SOLUTION_PARTIAL

    def _are_all_answers_correct(self):
        """Helper - checks if answers are all correct
        """
        return self.answers_correctness == self.SOLUTION_CORRECT

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench.
        """
        return [
            (
                'Drag-and-drop-v2 standard',
                '<vertical_demo><drag-and-drop-v2/></vertical_demo>'
            ),
            (
                'Drag-and-drop-v2 assessment',
                '<vertical_demo><drag-and-drop-v2 mode=\'assessment\' max_attempts=\'3\'/></vertical_demo>'
            ),
        ]
