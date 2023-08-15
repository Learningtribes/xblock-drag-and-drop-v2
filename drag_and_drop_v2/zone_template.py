# -*- coding: utf-8 -*-
"""
    With classes in this file we can extend drag and drop templates more easyier.
"""

import copy
from .utils import _, Constants, StateMigration


class ZonesDefinition(object):
    """Maintenance zones definitions ( generate or parse zones definition for user )

        Sample:
            {
                "zones": [
                    {
                        "uid": TOP_ZONE_ID,
                        "title": TOP_ZONE_TITLE, "description": TOP_ZONE_DESCRIPTION,
                        "x": 160, "y": 30, "width": 196, "height": 178, "align": "center"
                    }, ......
                ],
                "items": [
                    {
                        "id": 0, "displayName": ITEM_TOP_ZONE_NAME,
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
    START_FEEDBACK = 'Drag the items onto the image above.'      # We don't use this field anymore in our new version
    FINISH_FEEDBACK = 'Good work! You have completed this drag and drop problem.'
    _ITEM_CORRECT_FEEDBACK = 'Correct! This one belongs to {zone}.'
    _ITEM_INCORRECT_FEEDBACK = 'No, this item does not belong here. Try again.'

    def __init__(self, tpl_data=None):
        self._tpl_data = tpl_data

    def gen_zone_settings(self, uid, title, description, x, y, width, height, align):
        """Generate and return zone settings (dict) according to arguments
        """
        return {
            'uid': uid, 'title': title, 'description': description,
            'x': x, 'y': y, 'width': width, 'height': height, 'align': align
        }

    def gen_item_settings(self, id, display_name, incorrect_feedback, correct_feedback, related_zones, image_url):
        """Generate and return zone settings (dict) according to arguments
        """
        return {
            'id': id, 'displayName': display_name,
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

    def get_type_id(self):
        """Return zone template type id ( Integer )

            @return:            predefined type id of zone template
            @rtype:             Integer
        """
        return self._tpl_data['template_type'] if 'template_type' in self._tpl_data else 0

    def get_thumbnail_path(self):
        """Return thumbnail path"""
        return self._tpl_data['thumbnail'] if self._tpl_data else None

    def get_valid_zone_uids(self):
        """Return zones' uids List edited by User

            @return:            zone Keys
            @rtype:             list
        """
        if self._tpl_data is None:
            raise NotImplementedError('zones/items data is empty.')

        return [zone['uid'] for zone in self._tpl_data['zones']]

    def get_valid_item_ids(self):
        """Return all valid item IDs

            @return:            item ids
            @rtype:             set
        """
        if self._tpl_data is None:
            raise NotImplementedError('zones/items data is empty.')

        return set([str(item['id']) for item in self._tpl_data['items']])

    def get_zone_info_by_uid(self, uid):
        """Query & Return zone summary information by `zone uid`.

            @param uid:         uid value of a predefined zone
            @type uid:          string / integer
            @return:            predefined zone information
            @rtype:             dict
        """
        zone = [
            {'title': zone['title'], 'description': zone.get('description')} for zone in self._tpl_data['zones'] if uid == zone['uid']
        ]
        assert len(zone) == 1
        return zone[0]

    def is_attempt_correct(self, attempt, is_assessment_mod):
        """Check if the item was placed on correct area.
        """
        correct_zones = self.get_zones_by_item_id(attempt['val'])
        if correct_zones == [] and attempt['zone'] is None and is_assessment_mod:
            return True
        return attempt['zone'] in correct_zones

    def get_item_by_id(self, id):
        """Return item definition by `item id`
        """
        return next(_item for _item in self._tpl_data['items'] if _item['id'] == id)

    def get_zones_by_item_id(self, id):
        """Return item related zones by `id` in a zones `LIST`
        """
        _item = self.get_item_by_id(id)

        if _item.get('zones') is not None:
            return _item.get('zones')
        elif _item.get('zone') is not None and _item.get('zone') != 'none':
            return [_item.get('zone')]
        else:
            return []

    def get_zone_by_uid(self, uid):
        """Given a zone UID, return that zone, or None.
        """
        for _zone in self.get_compatible_zones():
            if _zone["uid"] == uid:
                return _zone

        return None

    def get_compatible_zones(self):
        """Get drop zone data, defined by the author.
            It's compatible with old format
        """
        # Convert zone data from old to new format if necessary
        return [
            StateMigration(self).apply_zone_migrations(zone) for zone in self._tpl_data.get('zones', [])
        ]

    def get_correct_state(self):
        """Returns one of the possible correct states for the configured data.
        """
        _state = {}
        _positions = {}

        for _item in copy.deepcopy(self._tpl_data.get('items', [])):
            zones = _item.get('zones')

            # For backwards compatibility
            if zones is None:
                zones = []
                zone = _item.get('zone')
                if zone is not None and zone != 'none':
                    zones.append(zone)

            if zones:
                zone = zones.pop()
                if zone not in _positions:
                    _positions[zone] = {'item_x': 0, 'item_y': 0}
                _state[str(_item['id'])] = {
                    'zone': zone,
                    'correct': True,
                    'item_x': _positions[zone]['item_x'],
                    'item_y': _positions[zone]['item_y']
                }
                _positions[zone]['item_x'] += 15
                _positions[zone]['item_y'] += 15

        return {'items': _state}

    def generate(self):
        """Generate and return template dict by settings in derived class
        """
        raise NotImplementedError


class TriangleTemplate(ZonesDefinition):
    """Predefined triangle template
    """
    TYPE_ID = 0
    THUMBNAIL_PATH = 'public/img/triangle.png'

    _TOP_ZONE_ID = "triangle_tpl_top"
    _MIDDLE_ZONE_ID = "triangle_tpl_middle"
    _BOTTOM_ZONE_ID = "triangle_tpl_bottom"
    _TOP_ZONE_TITLE = "The Top Zone"
    _MIDDLE_ZONE_TITLE = "The Middle Zone"
    _BOTTOM_ZONE_TITLE = "The Bottom Zone"

    _ITEM_TOP_ZONE_NAME = "Goes to the top"
    _ITEM_MIDDLE_ZONE_NAME = "Goes to the middle"
    _ITEM_BOTTOM_ZONE_NAME = "Goes to the bottom"
    _ITEM_ANY_ZONE_NAME = "Goes anywhere"
    _ITEM_NO_ZONE_NAME = "I don't belong anywhere"

    _ITEM_NO_ZONE_FEEDBACK = "You silly, there are no zones for this one."
    _ITEM_ANY_ZONE_FEEDBACK = "Of course it goes here! It goes anywhere!"

    def __init__(self, tpl_data=None):
        super(TriangleTemplate, self).__init__(tpl_data=tpl_data)

    def get_valid_zone_uids(self):
        """Return zones' uid List edited by User if user has stored zones definitions in MongoDB
            Otherwise return predefined zones' Key List

            @return:            zone Keys
            @rtype:             list
        """
        if self._tpl_data is None:
            return super(TriangleTemplate, self).get_valid_zone_uids()

        # Return predefined uids of zone.
        return [TriangleTemplate._TOP_ZONE_ID, TriangleTemplate._MIDDLE_ZONE_ID, TriangleTemplate._BOTTOM_ZONE_ID]

    def get_zone_info_by_uid(self, uid):
        """Query & Return zone summary information by `zone uid`. if user has stored zoned definitions in MongoDB
            Otherwise return predefined zones summary
        """
        if self._tpl_data is not None:
            return super(TriangleTemplate, self).get_zone_info_by_uid(uid)

        if uid == TriangleTemplate._TOP_ZONE_ID:
            return {'title': TriangleTemplate._TOP_ZONE_TITLE, 'description': None}
        elif uid == TriangleTemplate._MIDDLE_ZONE_ID:
            return {'title': TriangleTemplate._MIDDLE_ZONE_ID, 'description': None}
        elif uid == TriangleTemplate._BOTTOM_ZONE_ID:
            return {'title': TriangleTemplate._BOTTOM_ZONE_ID, 'description': None}

        raise KeyError('Invalie zone uid : {}'.format(uid))

    def generate(self):
        if self._tpl_data:
            return self._tpl_data

        self._tpl_data = {
            'zones': [
                self.gen_zone_settings(uid=self._TOP_ZONE_ID, title=self._TOP_ZONE_TITLE, description=None, x=160, y=30, width=196, height=180, align='none'),
                self.gen_zone_settings(uid=self._MIDDLE_ZONE_ID, title=self._MIDDLE_ZONE_TITLE, description=None, x=86, y=210, width=340, height=150, align='none'),
                self.gen_zone_settings(uid=self._BOTTOM_ZONE_ID, title=self._BOTTOM_ZONE_TITLE, description=None, x=15, y=360, width=485, height=140, align='none')
            ],
            'items': [
                self.gen_item_settings(id=0, display_name=self._ITEM_TOP_ZONE_NAME, incorrect_feedback=self._ITEM_INCORRECT_FEEDBACK, correct_feedback=self._ITEM_CORRECT_FEEDBACK.format(zone=self._TOP_ZONE_TITLE), related_zones=self._TOP_ZONE_ID, image_url=''),
                self.gen_item_settings(id=1, display_name=self._ITEM_MIDDLE_ZONE_NAME, incorrect_feedback=self._ITEM_INCORRECT_FEEDBACK, correct_feedback=self._ITEM_CORRECT_FEEDBACK.format(zone=self._MIDDLE_ZONE_TITLE), related_zones=self._MIDDLE_ZONE_ID, image_url=''),
                self.gen_item_settings(id=2, display_name=self._ITEM_BOTTOM_ZONE_NAME, incorrect_feedback=self._ITEM_INCORRECT_FEEDBACK, correct_feedback=self._ITEM_CORRECT_FEEDBACK.format(zone=self._BOTTOM_ZONE_TITLE), related_zones=self._BOTTOM_ZONE_ID, image_url=''),
                self.gen_item_settings(id=3, display_name=self._ITEM_ANY_ZONE_NAME, incorrect_feedback='', correct_feedback=self._ITEM_ANY_ZONE_FEEDBACK, related_zones=[self._TOP_ZONE_ID, self._BOTTOM_ZONE_ID, self._MIDDLE_ZONE_ID], image_url=''),
                self.gen_item_settings(id=4, display_name=self._ITEM_NO_ZONE_NAME, incorrect_feedback=self._ITEM_NO_ZONE_FEEDBACK, correct_feedback='', related_zones=[], image_url='')
            ],
            'feedback': self.gen_feedback(
                start=_(self.START_FEEDBACK),
                finish=_(self.FINISH_FEEDBACK)
            ),
            'thumbnail': self.THUMBNAIL_PATH,
            'template_type': self.TYPE_ID
        }

        return self._tpl_data


class RectangleTemplate(ZonesDefinition):
    """Predefined rectangle template
    """
    TYPE_ID = 1
    THUMBNAIL_PATH = 'public/img/rectangle.png'

    _LEFT_ZONE_ID = "two_rectangle_tpl_left"
    _RIGHT_ZONE_ID = "two_rectangle_tpl_right"

    _LEFT_ZONE_TITLE = "The Left Zone"
    _RIGHT_ZONE_TITLE = "The Right Zone"

    _ITEM_LEFT_ZONE_NAME = "Goes to the left"
    _ITEM_RIGHT_ZONE_NAME = "Goes to the right"
    _ITEM_ANY_ZONE_NAME = "Goes anywhere"
    _ITEM_NO_ZONE_NAME = "I don't belong anywhere"

    _ITEM_NO_ZONE_FEEDBACK = "You silly, there are no zones for this one."
    _ITEM_ANY_ZONE_FEEDBACK = "Of course it goes here! It goes anywhere!"

    def __init__(self, tpl_data=None):
        super(RectangleTemplate, self).__init__(tpl_data=tpl_data)

    def get_valid_zone_uids(self):
        """Return zones' uid List edited by User if user has stored zones definitions in MongoDB
            Otherwise return predefined zones' Key List

            @return:            zone Keys
            @rtype:             list
        """
        if self._tpl_data is None:
            return super(RectangleTemplate, self).get_valid_zone_uids()

        return [RectangleTemplate._LEFT_ZONE_ID, RectangleTemplate._RIGHT_ZONE_ID]

    def get_zone_info_by_uid(self, uid):
        """Query & Return zone summary information by `zone uid`. if user has stored zoned definitions in MongoDB
            Otherwise return predefined zones summary
        """
        if self._tpl_data is not None:
            return super(RectangleTemplate, self).get_zone_info_by_uid(uid)

        if uid == RectangleTemplate._LEFT_ZONE_ID:
            return {'title': RectangleTemplate._LEFT_ZONE_TITLE, 'description': None}
        elif uid == RectangleTemplate._RIGHT_ZONE_ID:
            return {'title': RectangleTemplate._RIGHT_ZONE_TITLE, 'description': None}

        raise KeyError('Invalid zone uid : {}'.format(uid))

    def generate(self):
        if self._tpl_data:
            return self._tpl_data

        self._tpl_data = {
            'zones': [
                self.gen_zone_settings(uid=self._LEFT_ZONE_ID, title=self._LEFT_ZONE_TITLE, description=None, x=0, y=0, width=470, height=498, align='none'),
                self.gen_zone_settings(uid=self._RIGHT_ZONE_ID, title=self._RIGHT_ZONE_TITLE, description=None, x=475, y=0, width=470, height=498, align='none'),
            ],
            'items': [
                self.gen_item_settings(id=0, display_name=self._ITEM_LEFT_ZONE_NAME, incorrect_feedback=self._ITEM_INCORRECT_FEEDBACK, correct_feedback=self._ITEM_CORRECT_FEEDBACK.format(zone=self._LEFT_ZONE_TITLE), related_zones=self._LEFT_ZONE_ID, image_url=''),
                self.gen_item_settings(id=1, display_name=self._ITEM_RIGHT_ZONE_NAME, incorrect_feedback=self._ITEM_INCORRECT_FEEDBACK, correct_feedback=self._ITEM_CORRECT_FEEDBACK.format(zone=self._RIGHT_ZONE_TITLE), related_zones=self._RIGHT_ZONE_ID, image_url=''),
                self.gen_item_settings(id=3, display_name=self._ITEM_ANY_ZONE_NAME, incorrect_feedback='', correct_feedback=self._ITEM_ANY_ZONE_FEEDBACK, related_zones=[self._LEFT_ZONE_ID, self._RIGHT_ZONE_ID], image_url=''),
                self.gen_item_settings(id=4, display_name=self._ITEM_NO_ZONE_NAME, incorrect_feedback=self._ITEM_NO_ZONE_FEEDBACK, correct_feedback='', related_zones=[], image_url='')
            ],
            'feedback': self.gen_feedback(
                start=_(self.START_FEEDBACK),
                finish=_(self.FINISH_FEEDBACK)
            ),
            'thumbnail': self.THUMBNAIL_PATH,
            'template_type': self.TYPE_ID
        }

        return self._tpl_data


class BlankTemplate(ZonesDefinition):
    """Predefined No background template
    """
    TYPE_ID = 2
    THUMBNAIL_PATH = 'public/img/triangle.png'

    def __init__(self, tpl_data=None):
        super(BlankTemplate, self).__init__(tpl_data=tpl_data)

    def generate(self):
        self._tpl_data = {
            'zones': [],
            'items': [],
            'feedback': self.gen_feedback(
                start=_(self.START_FEEDBACK),
                finish=_(self.FINISH_FEEDBACK)
            ),
            'thumbnail': self.THUMBNAIL_PATH,
            'template_type': self.TYPE_ID
        }
        return self._tpl_data


class CustomTemplate(ZonesDefinition):
    """Predefined custom template
    """
    TYPE_ID = 3

    def __init__(self, tpl_data=None):
        super(CustomTemplate, self).__init__(tpl_data=tpl_data)

    def generate(self):
        self._tpl_data = {
            'zones': [],
            'items': [],
            'feedback': self.gen_feedback(
                start=_(self.START_FEEDBACK),
                finish=_(self.FINISH_FEEDBACK)
            ),
            'thumbnail': '',
            'template_type': self.TYPE_ID
        }
        return self._tpl_data


class _ZoneTemplateDefinitions(object):
    """Definitions of zone templates used in drag and drop zone tab
    """
    ALL_SUPPORTED_TEMPLATES = [
        TriangleTemplate.TYPE_ID,
        RectangleTemplate.TYPE_ID,
        BlankTemplate.TYPE_ID,
        CustomTemplate.TYPE_ID
    ]

    def __init__(self):
        """Assemble predefined templates into dict object.
        """
        self._predefined_templates = {
            TriangleTemplate.TYPE_ID: TriangleTemplate().generate(),
            RectangleTemplate.TYPE_ID: RectangleTemplate().generate(),
            BlankTemplate.TYPE_ID: BlankTemplate().generate(),
            CustomTemplate.TYPE_ID: CustomTemplate().generate()
        }

    @property
    def predefined_templates(self):
        """Return templates data
        """
        return self._predefined_templates.values()

    def __iter__(self):
        return iter(self._predefined_templates.values())

    def get_templates_summary(self, xblock, runtime_local_resource_url):
        """Get templates' summary info for html rendering

            @param xblock:                          xblock instance
            @type xblock:                           XBlock derived class
            @param runtime_local_resource_url:      method `local_resource_url` of runtime instance
            @type runtime_local_resource_url:       method
            @return:                                templates summary info. list
            @rtype:                                 list
        """
        tpl_summaries = []

        for type_id, tpl_data in self._predefined_templates.items():
            tpl_summaries.append(
                {
                    'type_id': type_id,
                    'thumbnail': runtime_local_resource_url(xblock, tpl_data['thumbnail']) if tpl_data['thumbnail'] else '',
                    # Set background image for Triangle template only. Because other template are not predefined background image
                    'zones_background_image': xblock.pyramid_background_image_url if type_id == TriangleTemplate.TYPE_ID else None
                }
            )
        return tpl_summaries


ZONE_TPL_DEFINITIONS = _ZoneTemplateDefinitions()
