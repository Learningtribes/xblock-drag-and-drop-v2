# -*- coding: utf-8 -*-
"""
    With classes in this file we can extend drag and drop templates more easyier.
"""


from abc import ABCMeta, abstractmethod

from .utils import _


class _ZoneTemplatePolicy(object):
    """Abs Policy class of zone template

        Sample:
            {
                "zones": [
                    {
                        "key": TOP_ZONE_ID,
                        "title": TOP_ZONE_TITLE, "description": TOP_ZONE_DESCRIPTION,
                        "x": 160, "y": 30, "width": 196, "height": 178, "align": "center"
                    }, ......
                ],
                "items": [
                    {
                        "item_id": 0, "displayName": ITEM_TOP_ZONE_NAME,
                        "feedback": {
                            "incorrect": ITEM_INCORRECT_FEEDBACK,
                            "correct": ITEM_CORRECT_FEEDBACK.format(zone=TOP_ZONE_TITLE)
                        },
                        "zones": [ TOP_ZONE_ID ], "imageURL": ""
                    }, ......
                ],
                "feedback": { "start": START_FEEDBACK, "finish": FINISH_FEEDBACK },
                "thumbnail": "public/img/abc.jpg"
            }
    """
    __metaclass__ = ABCMeta

    def __init__(self, tpl_data=None):
        self._tpl_data = tpl_data

    def gen_zone_settings(self, key, title, description, x, y, width, height, align):
        """Generate and return zone settings (dict) according to arguments
        """
        return {
            'key': key, 'title': title, 'description': description,
            'x': x, 'y': y, 'width': width, 'height': height, 'align': align
        }

    def gen_item_settings(self, item_id, display_name, incorrect_feedback, correct_feedback, related_zones, image_url):
        """Generate and return zone settings (dict) according to arguments
        """
        return {
            'id': item_id, 'display_name': display_name,
            'feedback': {
                'incorrect': incorrect_feedback, 'correct': correct_feedback
            },
            'zones': related_zones if isinstance(related_zones, list) else [related_zones],
            'image_url': image_url
        }

    def gen_feedback(self, start, finish):
        """Generate and return feedback"""
        return {
            'start': start,
            'finish': finish
        }

    @classmethod
    def get_type_id(cls):
        """Return zone template type id ( Integer )

            @return:            predefined type id of zone template
            @rtype:             Integer
        """
        raise NotImplementedError

    @abstractmethod
    def get_thumbnail_path(self):
        """Return thumbnail path"""
        raise NotImplementedError

    @abstractmethod
    def get_valid_zone_keys(self):
        """Return all predefined zone keys ( List )

            @return:            predefined zone ids
            @rtype:             list
        """
        raise NotImplementedError

    @abstractmethod
    def get_zone_info_key(self, zone_key):
        """Return all predefined zone keys ( List )

            @param zone_key:    key value of a predefined zone
            @type zone_key:     string / integer
            @return:            predefined zone information
            @rtype:             dict
        """
        raise NotImplementedError

    @abstractmethod
    def generate(self):
        """Generate and return template dict by settings in derived class
        """
        raise NotImplementedError


class TriangleTemplate(_ZoneTemplatePolicy):
    """Predefined triangle template
    """
    _TOP_ZONE_ID = "top"
    _MIDDLE_ZONE_ID = "middle"
    _BOTTOM_ZONE_ID = "bottom"
    _TOP_ZONE_TITLE = _("The Top Zone")
    _MIDDLE_ZONE_TITLE = _("The Middle Zone")
    _BOTTOM_ZONE_TITLE = _("The Bottom Zone")

    _ITEM_TOP_ZONE_NAME = _("Goes to the top")
    _ITEM_MIDDLE_ZONE_NAME = _("Goes to the middle")
    _ITEM_BOTTOM_ZONE_NAME = _("Goes to the bottom")
    _ITEM_ANY_ZONE_NAME = _("Goes anywhere")
    _ITEM_NO_ZONE_NAME = _("I don't belong anywhere")

    _ITEM_CORRECT_FEEDBACK = _("Correct! This one belongs to {zone}.")
    _ITEM_INCORRECT_FEEDBACK = _("No, this item does not belong here. Try again.")
    _ITEM_NO_ZONE_FEEDBACK = _("You silly, there are no zones for this one.")
    _ITEM_ANY_ZONE_FEEDBACK = _("Of course it goes here! It goes anywhere!")

    def __init__(self, tpl_data=None):
        super(TriangleTemplate, self).__init__(tpl_data)

    @classmethod
    def get_type_id(cls):
        return 0

    def get_thumbnail_path(self):
        return 'public/img/triangle.png'

    def get_valid_zone_keys(self):
        return [_TOP_ZONE_ID, _MIDDLE_ZONE_ID, _BOTTOM_ZONE_ID]

    def get_zone_info_key(self, zone_key):
        if zone_key == _TOP_ZONE_ID:
            return {'title': _TOP_ZONE_TITLE, 'description': None}
        elif zone_key == _MIDDLE_ZONE_ID:
            return {'title': _MIDDLE_ZONE_ID, 'description': None}
        elif zone_key == _BOTTOM_ZONE_ID:
            return {'title': _BOTTOM_ZONE_ID, 'description': None}

        raise KeyError('Invalie zone key : {}'.format(zone_key))

    def generate(self):
        if self._tpl_data:
            return self._tpl_data

        self._tpl_data = {
            'zones': [
                self.gen_zone_settings(key=self._TOP_ZONE_ID, title=self._TOP_ZONE_TITLE, description=None, x=160, y=30, width=196, height=178, align='center'),
                self.gen_zone_settings(key=self._MIDDLE_ZONE_ID, title=self._MIDDLE_ZONE_TITLE, description=None, x=86, y=210, width=340, height=138, align='center'),
                self.gen_zone_settings(key=self._BOTTOM_ZONE_ID, title=self._BOTTOM_ZONE_TITLE, description=None, x=15, y=350, width=485, height=135, align='center')
            ],
            'items': [
                self.gen_item_settings(item_id=0, display_name=self._ITEM_TOP_ZONE_NAME, incorrect_feedback=self._ITEM_INCORRECT_FEEDBACK, correct_feedback=self._ITEM_CORRECT_FEEDBACK.format(zone=self._TOP_ZONE_TITLE), related_zones=self._TOP_ZONE_ID, image_url=''),
                self.gen_item_settings(item_id=1, display_name=self._ITEM_MIDDLE_ZONE_NAME, incorrect_feedback=self._ITEM_INCORRECT_FEEDBACK, correct_feedback=self._ITEM_CORRECT_FEEDBACK.format(zone=self._MIDDLE_ZONE_TITLE), related_zones=self._MIDDLE_ZONE_ID, image_url=''),
                self.gen_item_settings(item_id=2, display_name=self._ITEM_BOTTOM_ZONE_NAME, incorrect_feedback=self._ITEM_INCORRECT_FEEDBACK, correct_feedback=self._ITEM_CORRECT_FEEDBACK.format(zone=self._BOTTOM_ZONE_TITLE), related_zones=self._BOTTOM_ZONE_ID, image_url=''),
                self.gen_item_settings(item_id=3, display_name=self._ITEM_ANY_ZONE_NAME, incorrect_feedback='', correct_feedback=self._ITEM_ANY_ZONE_FEEDBACK, related_zones=[self._TOP_ZONE_ID, self._BOTTOM_ZONE_ID, self._MIDDLE_ZONE_ID], image_url=''),
                self.gen_item_settings(item_id=4, display_name=self._ITEM_NO_ZONE_NAME, incorrect_feedback=self._ITEM_NO_ZONE_FEEDBACK, correct_feedback='', related_zones=[], image_url='')
            ],
            'feedback': self.gen_feedback(
                start=_("Drag the items onto the image above."),
                finish=_("Good work! You have completed this drag and drop problem.")
            ),
            'thumbnail': self.get_thumbnail_path()
        }

        return self._tpl_data


class RectangleTemplate(_ZoneTemplatePolicy):
    """Predefined rectangle template
    """
    _TOP_ZONE_ID = "top"
    _MIDDLE_ZONE_ID = "middle"
    _BOTTOM_ZONE_ID = "bottom"
    _TOP_ZONE_TITLE = _("The Top Zone")
    _MIDDLE_ZONE_TITLE = _("The Middle Zone")
    _BOTTOM_ZONE_TITLE = _("The Bottom Zone")

    _ITEM_TOP_ZONE_NAME = _("Goes to the top")
    _ITEM_MIDDLE_ZONE_NAME = _("Goes to the middle")
    _ITEM_BOTTOM_ZONE_NAME = _("Goes to the bottom")
    _ITEM_ANY_ZONE_NAME = _("Goes anywhere")
    _ITEM_NO_ZONE_NAME = _("I don't belong anywhere")

    _ITEM_CORRECT_FEEDBACK = _("Correct! This one belongs to {zone}.")
    _ITEM_INCORRECT_FEEDBACK = _("No, this item does not belong here. Try again.")
    _ITEM_NO_ZONE_FEEDBACK = _("You silly, there are no zones for this one.")
    _ITEM_ANY_ZONE_FEEDBACK = _("Of course it goes here! It goes anywhere!")

    def __init__(self, tpl_data=None):
        super(RectangleTemplate, self).__init__(tpl_data)

    @classmethod
    def get_type_id(self):
        return 1

    def get_thumbnail_path(self):
        return 'public/img/hat.png'

    def get_valid_zone_keys(self):
        return [_TOP_ZONE_ID, _MIDDLE_ZONE_ID, _BOTTOM_ZONE_ID]

    def get_zone_info_key(self, zone_key):
        if zone_key == _TOP_ZONE_ID:
            return {'title': _TOP_ZONE_TITLE, 'description': None}
        elif zone_key == _MIDDLE_ZONE_ID:
            return {'title': _MIDDLE_ZONE_ID, 'description': None}
        elif zone_key == _BOTTOM_ZONE_ID:
            return {'title': _BOTTOM_ZONE_ID, 'description': None}

        raise KeyError('Invalid zone key : {}'.format(zone_key))

    def generate(self):
        if self._tpl_data:
            return self._tpl_data

        self._tpl_data = {
            'zones': [
                self.gen_zone_settings(key=self._TOP_ZONE_ID, title=self._TOP_ZONE_TITLE, description=None, x=160, y=30, width=196, height=178, align='center'),
                self.gen_zone_settings(key=self._MIDDLE_ZONE_ID, title=self._MIDDLE_ZONE_TITLE, description=None, x=86, y=210, width=340, height=138, align='center'),
                self.gen_zone_settings(key=self._BOTTOM_ZONE_ID, title=self._BOTTOM_ZONE_TITLE, description=None, x=15, y=350, width=485, height=135, align='center')
            ],
            'items': [
                self.gen_item_settings(item_id=0, display_name=self._ITEM_TOP_ZONE_NAME, incorrect_feedback=self._ITEM_INCORRECT_FEEDBACK, correct_feedback=self._ITEM_CORRECT_FEEDBACK.format(zone=self._TOP_ZONE_TITLE), related_zones=self._TOP_ZONE_ID, image_url=''),
                self.gen_item_settings(item_id=1, display_name=self._ITEM_MIDDLE_ZONE_NAME, incorrect_feedback=self._ITEM_INCORRECT_FEEDBACK, correct_feedback=self._ITEM_CORRECT_FEEDBACK.format(zone=self._MIDDLE_ZONE_TITLE), related_zones=self._MIDDLE_ZONE_ID, image_url=''),
                self.gen_item_settings(item_id=2, display_name=self._ITEM_BOTTOM_ZONE_NAME, incorrect_feedback=self._ITEM_INCORRECT_FEEDBACK, correct_feedback=self._ITEM_CORRECT_FEEDBACK.format(zone=self._BOTTOM_ZONE_TITLE), related_zones=self._BOTTOM_ZONE_ID, image_url=''),
                self.gen_item_settings(item_id=3, display_name=self._ITEM_ANY_ZONE_NAME, incorrect_feedback='', correct_feedback=self._ITEM_ANY_ZONE_FEEDBACK, related_zones=[self._TOP_ZONE_ID, self._BOTTOM_ZONE_ID, self._MIDDLE_ZONE_ID], image_url=''),
                self.gen_item_settings(item_id=4, display_name=self._ITEM_NO_ZONE_NAME, incorrect_feedback=self._ITEM_NO_ZONE_FEEDBACK, correct_feedback='', related_zones=[], image_url='')
            ],
            'feedback': self.gen_feedback(
                start=_("Drag the items onto the image above."),
                finish=_("Good work! You have completed this drag and drop problem.")
            ),
            'thumbnail': self.get_thumbnail_path()
        }

        return self._tpl_data


class _ZoneTemplateDefinitions(object):
    """Definitions of zone templates used in drag and drop zone tab
    """
    ALL_SUPPORTED_TEMPLATES = [TriangleTemplate.get_type_id(), RectangleTemplate.get_type_id()]

    def __init__(self):
        """Assemble predefined templates into dict object.
        """
        self._predefined_templates = {
            TriangleTemplate.get_type_id(): TriangleTemplate().generate(),
            RectangleTemplate.get_type_id(): RectangleTemplate().generate()
        }

    def get_predefined_template_by_type(self, tpl_id):
        """Return template by type id
        """
        if tpl_type not in ZoneTemplate.ALL_SUPPORTED_TEMPLATES or tpl_type not in self._predefined_templates:
            raise NotImplementedError('Got invalid template type value : {}'.format(tpl_type))

        return self._predefined_templates[tpl_id]

    def __iter__(self):
        return iter(self._predefined_templates.values())

    def get_templates_summary(self, xblock, runtime_local_resource_url):
        """
            @param xblock:                          xblock instance
            @type xblock:                           XBlock derived class
            @param runtime_local_resource_url:      method `local_resource_url` of runtime instance
            @type runtime_local_resource_url:       method
            @return:                                templates summary info. list
            @rtype:                                 list
        """
        return [{'type_id': type_id, 'thumbnail': runtime_local_resource_url(xblock, tpl_data['thumbnail'])} for type_id, tpl_data in self._predefined_templates.items()]


ZONE_TPL_DEFINITIONS = _ZoneTemplateDefinitions()
