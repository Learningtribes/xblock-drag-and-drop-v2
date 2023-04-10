# -*- coding: utf-8 -*-


class TabsHeader(object):
    """Definitions of Tabs bar used on the top of draft_drop component editor
    """
    class _Tab(object):
        def __init__(self, tab_name, tab_id):
            self._tab_name = tab_name
            self._tab_id = tab_id

        @property
        def id(self):
            return self._tab_id

        @property
        def name(self):
            return self._tab_name

    def __init__(self):
        self._tabs = [
            TabsHeader._Tab('SETTINGS', tab_id=0),
            TabsHeader._Tab('BACKGROUND', tab_id=1),
            TabsHeader._Tab('ZONES', tab_id=2),
            TabsHeader._Tab('ANSWERS', tab_id=3)
        ]

    def __iter__(self):
        """Return an iterable object"""
        return iter(self._tabs)

