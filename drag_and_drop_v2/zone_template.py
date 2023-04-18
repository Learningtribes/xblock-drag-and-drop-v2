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
                "feedback": { "start": START_FEEDBACK, "finish": FINISH_FEEDBACK }
            }
    """
    __metaclass__ = ABCMeta

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

    @classmethod
    def get_type_id(cls):
        return 0

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
        return {
            'zones': [
                self.gen_zone_settings(key=_TOP_ZONE_ID, title=_TOP_ZONE_TITLE, description=None, x=160, y=30, width=196, height=178, align='center'),
                self.gen_zone_settings(key=_MIDDLE_ZONE_ID, title=_MIDDLE_ZONE_TITLE, description=None, x=86, y=210, width=340, height=138, align='center'),
                self.gen_zone_settings(key=_BOTTOM_ZONE_ID, title=_BOTTOM_ZONE_TITLE, description=None, x=15, y=350, width=485, height=135, align='center')
            ],
            'items': [
                self.gen_item_settings(item_id=0, display_name=_ITEM_TOP_ZONE_NAME, incorrect_feedback=_ITEM_INCORRECT_FEEDBACK, correct_feedback=_ITEM_CORRECT_FEEDBACK.format(zone=_TOP_ZONE_TITLE), related_zones=_TOP_ZONE_ID, image_url=''),
                self.gen_item_settings(item_id=1, display_name=_ITEM_MIDDLE_ZONE_NAME, incorrect_feedback=_ITEM_INCORRECT_FEEDBACK, correct_feedback=_ITEM_CORRECT_FEEDBACK.format(zone=_MIDDLE_ZONE_TITLE), related_zones=_MIDDLE_ZONE_ID, image_url=''),
                self.gen_item_settings(item_id=2, display_name=_ITEM_BOTTOM_ZONE_NAME, incorrect_feedback=_ITEM_INCORRECT_FEEDBACK, correct_feedback=_ITEM_CORRECT_FEEDBACK.format(zone=_BOTTOM_ZONE_TITLE), related_zones=_BOTTOM_ZONE_ID, image_url=''),
                self.gen_item_settings(item_id=3, display_name=_ITEM_ANY_ZONE_NAME, incorrect_feedback='', correct_feedback=_ITEM_ANY_ZONE_FEEDBACK, related_zones=[_TOP_ZONE_ID, _BOTTOM_ZONE_ID, _MIDDLE_ZONE_ID], image_url=''),
                self.gen_item_settings(item_id=4, display_name=_ITEM_NO_ZONE_NAME, incorrect_feedback=_ITEM_NO_ZONE_FEEDBACK, correct_feedback='', related_zones=[], image_url='')
            ],
            'feedback': self.gen_feedback(
                start=_("Drag the items onto the image above."),
                finish=_("Good work! You have completed this drag and drop problem.")
            )
        }


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

    @classmethod
    def get_type_id(self):
        return 1

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
        return {
            'zones': [
                self.gen_zone_settings(key=_TOP_ZONE_ID, title=_TOP_ZONE_TITLE, description=None, x=160, y=30, width=196, height=178, align='center'),
                self.gen_zone_settings(key=_MIDDLE_ZONE_ID, title=_MIDDLE_ZONE_TITLE, description=None, x=86, y=210, width=340, height=138, align='center'),
                self.gen_zone_settings(key=_BOTTOM_ZONE_ID, title=_BOTTOM_ZONE_TITLE, description=None, x=15, y=350, width=485, height=135, align='center')
            ],
            'items': [
                self.gen_item_settings(item_id=0, display_name=_ITEM_TOP_ZONE_NAME, incorrect_feedback=_ITEM_INCORRECT_FEEDBACK, correct_feedback=_ITEM_CORRECT_FEEDBACK.format(zone=_TOP_ZONE_TITLE), related_zones=_TOP_ZONE_ID, image_url=''),
                self.gen_item_settings(item_id=1, display_name=_ITEM_MIDDLE_ZONE_NAME, incorrect_feedback=_ITEM_INCORRECT_FEEDBACK, correct_feedback=_ITEM_CORRECT_FEEDBACK.format(zone=_MIDDLE_ZONE_TITLE), related_zones=_MIDDLE_ZONE_ID, image_url=''),
                self.gen_item_settings(item_id=2, display_name=_ITEM_BOTTOM_ZONE_NAME, incorrect_feedback=_ITEM_INCORRECT_FEEDBACK, correct_feedback=_ITEM_CORRECT_FEEDBACK.format(zone=_BOTTOM_ZONE_TITLE), related_zones=_BOTTOM_ZONE_ID, image_url=''),
                self.gen_item_settings(item_id=3, display_name=_ITEM_ANY_ZONE_NAME, incorrect_feedback='', correct_feedback=_ITEM_ANY_ZONE_FEEDBACK, related_zones=[_TOP_ZONE_ID, _BOTTOM_ZONE_ID, _MIDDLE_ZONE_ID], image_url=''),
                self.gen_item_settings(item_id=4, display_name=_ITEM_NO_ZONE_NAME, incorrect_feedback=_ITEM_NO_ZONE_FEEDBACK, correct_feedback='', related_zones=[], image_url='')
            ],
            'feedback': self.gen_feedback(
                start=_("Drag the items onto the image above."),
                finish=_("Good work! You have completed this drag and drop problem.")
            )
        }


class ZoneTemplateDefinitions(object):
    """Definitions of zone templates used in drag and drop zone tab
    """
    ALL_SUPPORTED_TEMPLATES = [TriangleTemplate.get_type_id(), RectangleTemplate.get_type_id()]

    def __init__(self):
        """Assemble predefined templates
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
