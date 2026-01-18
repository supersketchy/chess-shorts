import json
from google import genai
from puzzle import Puzzle
from story import Character, Emotion, StoryBeat, Story
import config

CHARACTER_GIFS: dict[tuple[Character, Emotion], str] = {
    (Character.MAGNUS, Emotion.ANGRY): "magnus_angry.gif",
    (Character.MAGNUS, Emotion.EXCITED): "magnus_excited.gif",
    (Character.MAGNUS, Emotion.SHOCKED): "magnus_shocked.gif",
    (Character.MAGNUS, Emotion.SURPRISED): "magnus_suprised.gif",
    (Character.HIKARU, Emotion.CALCULATING): "hikaru_calculating.gif",
    (Character.HIKARU, Emotion.EXCITED): "hikaru_excited.gif",
    (Character.HIKARU, Emotion.SHOCKED): "hikaru_shocked.gif",
    (Character.HIKARU, Emotion.UPSET): "hikaru_upset.gif",
}

EMOTION_AUDIO: dict[Emotion, str] = {
    Emotion.CALCULATING: "vine-boom.mp3",
    Emotion.EXCITED: "baby-laughing-meme.mp3",
    Emotion.SHOCKED: "anime-wow-sound-effect.mp3",
    Emotion.UPSET: "why-are-you-running.mp3",
    Emotion.ANGRY: "get-out-sound.mp3",
    Emotion.SURPRISED: "anime-wow-sound-effect.mp3",
}

AUDIO_DURATIONS: dict[str, float] = {
    "anime-wow-sound-effect.mp3": 2.8,
    "baby-laughing-meme.mp3": 4.4,
    "get-out-sound.mp3": 1.8,
    "vine-boom.mp3": 0.9,
    "why-are-you-running.mp3": 4.4,
}

GIF_DURATIONS: dict[str, float] = {
    "hikaru_calculating.gif": 6.04,
    "hikaru_excited.gif": 5.11,
    "hikaru_shocked.gif": 6.60,
    "hikaru_upset.gif": 6.71,
    "magnus_angry.gif": 4.81,
    "magnus_excited.gif": 1.74,
    "magnus_shocked.gif": 3.01,
    "magnus_suprised.gif": 2.24,
}


def _build_prompt(puzzle: Puzzle, num_moves: int) -> str:
    """Build Gemini prompt for story generation.

    Args:
        puzzle (Puzzle): The chess puzzle.
        num_moves (int): Number of moves in the puzzle.

    Returns:
        str: The formatted prompt.
    """
    available_gifs_with_durations = {f"{k[0].value}_{k[1].value}": {"file": v, "duration": GIF_DURATIONS.get(v, 3.0)} for k, v in CHARACTER_GIFS.items()}
    available_audio = {k.value: {"file": v, "duration": AUDIO_DURATIONS[v]} for k, v in EMOTION_AUDIO.items()}

    return f"""You are a chess content creator making a dramatic 60-second YouTube Short about a chess puzzle.

Puzzle Details:
- FEN: {puzzle.fen}
- Moves: {" ".join(puzzle.moves)}
- Number of moves: {num_moves}

Create a dramatic story with Magnus Carlsen vs Hikaru Nakamura reacting to the puzzle moves.

Available Character GIFs (with durations in seconds):
{json.dumps(available_gifs_with_durations, indent=2)}

Available Audio (with durations in seconds):
{json.dumps(available_audio, indent=2)}

Generate a JSON response with story beats. Each beat should:
1. Alternate between Magnus and Hikaru
2. Match emotions to puzzle tension (calculating early, shocked at key moves, excited/upset at resolution)
3. Use move_index to sync with chess moves (0 to {num_moves - 1})
4. Total duration should be approximately {config.target_video_duration} seconds
5. IMPORTANT: Set each beat's duration to be a multiple of both the GIF duration and audio duration for that emotion. This ensures smooth looping. For example, if a GIF is 3.0s and audio is 0.9s, use 9.0s (3x GIF, 10x audio).

Response format:
{{
    "title": "Brief dramatic title",
    "beats": [
        {{
            "character": "magnus" or "hikaru",
            "emotion": "calculating" | "excited" | "shocked" | "upset" | "angry" | "surprised",
            "move_index": 0,
            "duration": 9.0
        }}
    ]
}}

Make sure beats cover all moves and create dramatic tension. Start slow, build to climax at the key move, then resolution."""


def _parse_response(response_text: str, puzzle: Puzzle) -> Story:
    """Parse Gemini response into Story object.

    Args:
        response_text (str): JSON response from Gemini.
        puzzle (Puzzle): The chess puzzle.

    Returns:
        Story: Parsed story with timed beats.
    """
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    data = json.loads(text.strip())
    beats: list[StoryBeat] = []
    current_time = 0.0

    for beat_data in data["beats"]:
        character = Character(beat_data["character"])
        emotion = Emotion(beat_data["emotion"])
        duration = float(beat_data["duration"])
        move_index = int(beat_data["move_index"])

        gif_key = (character, emotion)
        gif_name = CHARACTER_GIFS.get(gif_key, list(CHARACTER_GIFS.values())[0])
        audio_name = EMOTION_AUDIO.get(emotion, "vine-boom.mp3")

        beats.append(
            StoryBeat(
                character=character,
                emotion=emotion,
                gif_name=gif_name,
                audio_name=audio_name,
                start_time=current_time,
                duration=duration,
                move_index=move_index,
            )
        )
        current_time += duration

    return Story(
        puzzle_id=puzzle.puzzle_id,
        title=data.get("title", "Chess Puzzle"),
        beats=beats,
        total_duration=current_time,
    )


def generate_fallback_story(puzzle: Puzzle) -> Story:
    """Generate story without API by alternating characters.

    Args:
        puzzle (Puzzle): The chess puzzle.

    Returns:
        Story: A simple alternating story.
    """
    num_moves = len(puzzle.moves)
    beat_duration = config.target_video_duration / max(num_moves, 1)
    beats: list[StoryBeat] = []
    current_time = 0.0

    emotions_sequence = [Emotion.CALCULATING, Emotion.SHOCKED, Emotion.EXCITED, Emotion.UPSET, Emotion.ANGRY, Emotion.SURPRISED]

    for i in range(num_moves):
        character = Character.MAGNUS if i % 2 == 0 else Character.HIKARU
        emotion = emotions_sequence[i % len(emotions_sequence)]

        gif_key = (character, emotion)
        if gif_key not in CHARACTER_GIFS:
            available_for_char = [k for k in CHARACTER_GIFS.keys() if k[0] == character]
            gif_key = available_for_char[i % len(available_for_char)] if available_for_char else list(CHARACTER_GIFS.keys())[0]

        gif_name = CHARACTER_GIFS[gif_key]
        audio_name = EMOTION_AUDIO.get(gif_key[1], "vine-boom.mp3")

        beats.append(
            StoryBeat(
                character=character,
                emotion=gif_key[1],
                gif_name=gif_name,
                audio_name=audio_name,
                start_time=current_time,
                duration=beat_duration,
                move_index=i,
            )
        )
        current_time += beat_duration

    return Story(
        puzzle_id=puzzle.puzzle_id,
        title="Chess Puzzle Challenge",
        beats=beats,
        total_duration=current_time,
    )


def generate_story(puzzle: Puzzle) -> Story:
    """Generate story using Gemini API or fallback.

    Args:
        puzzle (Puzzle): The chess puzzle.

    Returns:
        Story: Generated story with timed beats.
    """
    if not config.gemini_api_key:
        return generate_fallback_story(puzzle)

    client = genai.Client(api_key=config.gemini_api_key)

    num_moves = len(puzzle.moves)
    prompt = _build_prompt(puzzle, num_moves)

    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    return _parse_response(response.text, puzzle)
