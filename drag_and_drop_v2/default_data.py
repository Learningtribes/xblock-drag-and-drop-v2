""" Default data for Drag and Drop v2 XBlock """
from .utils import _

TARGET_IMG_DESCRIPTION = _(
    "An isosceles triangle with three layers of similar height. "
    "It is shown upright, so the widest layer is located at the bottom, "
    "and the narrowest layer is located at the top."
)

TOP_ZONE_ID = "top"
MIDDLE_ZONE_ID = "middle"
BOTTOM_ZONE_ID = "bottom"

TOP_ZONE_TITLE = "The Top Zone"
MIDDLE_ZONE_TITLE = "The Middle Zone"
BOTTOM_ZONE_TITLE = "The Bottom Zone"

TOP_ZONE_DESCRIPTION = "Use this zone to associate an item with the top layer of the triangle."
MIDDLE_ZONE_DESCRIPTION = "Use this zone to associate an item with the middle layer of the triangle."
BOTTOM_ZONE_DESCRIPTION = "Use this zone to associate an item with the bottom layer of the triangle."

ITEM_CORRECT_FEEDBACK = "Correct! This one belongs to {zone}."
ITEM_INCORRECT_FEEDBACK = "No, this item does not belong here. Try again."
ITEM_NO_ZONE_FEEDBACK = "You silly, there are no zones for this one."
ITEM_ANY_ZONE_FEEDBACK = "Of course it goes here! It goes anywhere!"

ITEM_TOP_ZONE_NAME = "Goes to the top"
ITEM_MIDDLE_ZONE_NAME = "Goes to the middle"
ITEM_BOTTOM_ZONE_NAME = "Goes to the bottom"
ITEM_ANY_ZONE_NAME = "Goes anywhere"
ITEM_NO_ZONE_NAME = "I don't belong anywhere"

START_FEEDBACK = "Drag the items onto the image above."
FINISH_FEEDBACK = "Good work! You have completed this drag and drop problem."


DEFAULT_EMPTY_DATA = {
    'template_type': None,
    'targetImgDescription': '',
    'zones': [],
    'items': [],
    'feedback': {
        'start': '',
        'finish': '',
    },
}
