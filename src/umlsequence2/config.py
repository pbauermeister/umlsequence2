"""Configuration definitions and declaration.

All size and style values are set here.

"""

from . import model


# Dimensions are in cm.
_CONFIG = model.Config(
    ACTIVITY_WIDTH  = 0.20,

    ACTOR_ASCENT    = 0.25,
    ACTOR_DESCENT   = 0.45,
    ACTOR_LABEL_Y   = 0.90,

    ARROW_HEAD_SIZE = 0.30,

    COLOR_GREY      = '#aaaaaa',

    COLUMN_SPACING  = 0.25,
    COLUMN_WIDTH    = 2.75,

    CROSS_SIZE      = 0.50,

    MESSAGE_SPACING = 0.05,

    OBJECT_HEIGHT   = 0.60,
    OBJECT_LABEL_Y  = 0.40,
    OBJECT_STEP     = 0.90,

    STEP_NORMAL     = 0.60,
    STEP_SMALL      = 0.30,

    TEXT_CHAR_WIDTH = 0.145,
    TEXT_DOGEAR     = 0.20,
    TEXT_HEIGHT     = 0.40,
    TEXT_FONT       = dict(font_family='Helvetica, Arial, sans-serif',
                           font_size='10px'),
    TEXT_MARGIN_X   = 0.20,
    TEXT_MARGIN_Y   = 0.15,
)


def set_config(cfg: model.Config) -> None:
    global _CONFIG
    _CONFIG = cfg


def get_config() -> model.Config:
    return _CONFIG
