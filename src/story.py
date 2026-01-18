from enum import Enum
from typing import NamedTuple


class Character(Enum):
    """Chess player characters.

    Attributes:
        MAGNUS: Magnus Carlsen.
        HIKARU: Hikaru Nakamura.
    """

    MAGNUS = "magnus"
    HIKARU = "hikaru"


class Emotion(Enum):
    """Emotional states for reactions.

    Attributes:
        CALCULATING: Deep focus/thinking.
        EXCITED: Happy/celebratory.
        SHOCKED: Stunned/disbelief.
        UPSET: Disappointed/sad.
        ANGRY: Frustrated/mad.
        SURPRISED: Caught off guard.
    """

    CALCULATING = "calculating"
    EXCITED = "excited"
    SHOCKED = "shocked"
    UPSET = "upset"
    ANGRY = "angry"
    SURPRISED = "surprised"


class StoryBeat(NamedTuple):
    """A single beat in the story narrative.

    Attributes:
        character (Character): The character reacting.
        emotion (Emotion): The emotional state.
        gif_name (str): GIF filename to use.
        audio_name (str): Audio filename to use.
        start_time (float): Start time in seconds.
        duration (float): Duration in seconds.
        move_index (int): Chess move index for this beat.
    """

    character: Character
    emotion: Emotion
    gif_name: str
    audio_name: str
    start_time: float
    duration: float
    move_index: int


class Story(NamedTuple):
    """Complete story for a chess puzzle video.

    Attributes:
        puzzle_id (str): The puzzle identifier.
        title (str): Story title/description.
        beats (list[StoryBeat]): Sequence of story beats.
        total_duration (float): Total video duration in seconds.
    """

    puzzle_id: str
    title: str
    beats: list[StoryBeat]
    total_duration: float
