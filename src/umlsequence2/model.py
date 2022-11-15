from dataclasses import dataclass
from typing import Any


@dataclass
class Config:
    ACTIVITY_WIDTH:  float

    ACTOR_ASCENT:    float
    ACTOR_DESCENT:   float
    ACTOR_LABEL_Y:   float

    ARROW_HEAD_SIZE: float

    COLOR_GREY:      str

    COLUMN_SPACING:  float
    COLUMN_WIDTH:    float

    CROSS_SIZE:      float

    MESSAGE_SPACING: float

    OBJECT_HEIGHT:   float
    OBJECT_LABEL_Y:  float
    OBJECT_STEP:     float

    STEP_NORMAL:     float
    STEP_SMALL:      float

    TEXT_CHAR_WIDTH: float
    TEXT_DOGEAR:     float
    TEXT_FONT:       dict[str, str]
    TEXT_HEIGHT:     float
    TEXT_MARGIN_X:   float
    TEXT_MARGIN_Y:   float


class UmlSequenceError(Exception):
    pass


@dataclass
class Command:
    cmd: str
    args: list[Any]


@dataclass
class Element: pass


@dataclass
class Object(Element):
    type:  str
    index: int
    name:  str
    label: str
    ypos:  float
    row:   int


@dataclass
class Comment(Element):
    x:      float
    y:      float
    width:  float
    height: float


@dataclass
class Frame(Element):
    xpos:  float
    ypos:  float
    label: str
    out:   float


@dataclass
class Rectangle:
    x: float
    y: float
    w: float
    h: float
