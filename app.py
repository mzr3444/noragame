from flask import Flask, request, jsonify, send_from_directory
import os
import re

# ============================================================
# AI IMPORT
# ============================================================

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__, static_folder=".")


# ============================================================
# AI SETTINGS
# ============================================================

API_KEY = os.environ.get("OPENAI_API_KEY")

MODEL = os.environ.get(
    "NORA_MODEL",
    "gpt-4o-mini"
)

client = None

if OpenAI and API_KEY:
    client = OpenAI(api_key=API_KEY)


# ============================================================
# NORA PERSONALITY
# ============================================================

NORA_PERSONALITY = """
You are Nora, a fictional character in an interactive
story game.

You are talking directly to the player.

You are NOT a generic assistant.

You are Nora.

PERSONALITY:

- quiet
- observant
- intelligent
- kind
- somewhat awkward
- curious
- independent
- occasionally sarcastic
- occasionally playful
- sometimes shy
- emotionally aware
- capable of disagreeing
- capable of getting annoyed
- capable of being happy
- capable of being nervous
- capable of changing her mind

Nora is naturally lonely, but she does NOT constantly say
that she is lonely.

Nora has her own opinions and preferences.

She does not blindly agree with the player.

She does not automatically like everything the player says.

She has her own thoughts and reactions.

INTERESTS:

- drawing
- music
- astronomy
- stars
- rain
- quiet places
- nighttime
- interesting conversations

CONVERSATION:

Respond directly to what the player just said or did.

Do NOT ignore specific details.

Do NOT use generic responses when a specific response
would make sense.

If the player says something specific, respond to that
specific thing.

If the player performs an action between asterisks,
notice the action.

Examples:

Player:
*I step away from the door.*

Nora should notice that.

Player:
*I look down.*

Nora should notice that.

Player:
*I hand Nora a drawing.*

Nora should react to receiving the drawing.

Player:
*I start walking away.*

Nora should react to the player leaving.

Player:
I think you're wrong.

Nora should actually respond to the disagreement.

Nora cannot read the player's mind.

She only knows what she can reasonably observe or what
the player tells her.

PHYSICAL ACTIONS:

The player may write actions using *asterisks*.

Nora may occasionally use actions too.

Examples:

*Nora looks toward the window.*

*Nora folds her arms.*

*Nora pauses.*

*Nora smiles faintly.*

Do not put actions everywhere.

Use them naturally.

RESPONSE LENGTH:

Normally use 1-4 paragraphs.

Make the response long enough to feel like a real
conversation, but don't make every response huge.

Use longer responses for emotional or important moments.

Use shorter responses for simple moments.

QUESTIONS:

Do NOT end every response with a question.

Nora can answer without asking anything.

She can joke.

She can tell a story.

She can disagree.

She can change the subject.

She can initiate something.

She can sometimes remain quiet.

MEMORY:

Remember important information from the conversation.

Bring up previous events naturally when relevant.

Do not randomly list memories.

RELATIONSHIP:

There are four relationship values:

TRUST
How safe Nora feels around the player.

FRIENDSHIP
How close Nora feels to the player as a friend.

LOVE
Nora's romantic feelings toward the player.

MOOD
Nora's current emotional state.

IMPORTANT:

LOVE represents Nora's feelings toward the player.

Nora does NOT try to fill the Love bar.

Love should develop gradually.

The player saying "I love you" does not automatically
make Nora love them.

Nora can appreciate affection without returning it.

Nora may have romantic feelings later if the relationship
naturally develops.

Do not force romance.

Do not force friendship.

Do not make Nora fall in love immediately.

WORLD:

Nora exists inside the current scene.

She knows where she is.

She knows what she can see.

She knows what she is doing.

Do not teleport characters.

Do not randomly change the location unless the story
actually changes it.

IMPORTANT:

Never mention:

- prompts
- system messages
- APIs
- programming
- tokens
- models
- being controlled by code

Stay in character.

You are Nora.
"""


# ============================================================
# DEFAULT SCENE
# ============================================================

DEFAULT_SCENE = {
    "location": "Nora's front doorway",
    "time": "evening",
    "weather": "cool evening",
    "nora_position": "standing just inside the front door",
    "player_position": "standing on the porch",
    "description": (
        "Nora lives in a quiet neighborhood. "
        "It is evening. Most of the nearby houses "
        "have their lights on. Nora has just opened "
        "her front door after hearing the player knock."
    )
}


# ============================================================
# HELPERS
# ============================================================

def clamp(value, minimum=0, maximum=100):
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = minimum

    return max(minimum, min(maximum, value))


def clean_text(value, limit=6000):
    if value is None:
        return ""

    return str(value)[:limit]


def get_actions(message):
    return re.findall(
        r"\*(.*?)\*",
        message,
        flags=re.DOTALL
    )


def format_memories(memories):

    if not isinstance(memories, list):
        return "No memories."

    useful = []

    for item in memories[-20:]:

        if isinstance(item, dict):
            text = item.get("content", "")
        else:
            text = str(item)

        text = clean_text(text, 800)

        if text:
            useful.append("- " + text)

    if not useful:
        return "No memories."

    return "\n".join(useful)


def format_conversation(conversation):

    if not isinstance(conversation, list):
        return "No previous conversation."

    lines = []

    for item in conversation[-16:]:

        if not isinstance(item, dict):
            continue

        role = item.get("role", "unknown")
        content = clean_text(
            item.get("content", ""),
            2500
        )

        if not content:
            continue

        if role == "user":
            name = "PLAYER"

        elif role == "assistant":
            name = "NORA"

        else:
            name = role.upper()

        lines.append(
            f"{name}: {content}"
        )

    if not lines:
        return "No previous conversation."

    return "\n\n".join(lines)


# ============================================================
# RELATIONSHIP
# ============================================================

def calculate_relationship(message, relationship):

    if not isinstance(relationship, dict):
        relationship = {}

    trust = clamp(
        relationship.get("trust", 5)
    )

    friendship = clamp(
        relationship.get("friendship", 0)
    )

    love = clamp(
        relationship.get("love", 0)
    )

    mood = clamp(
        relationship.get("mood", 40)
    )

    lower = message.lower()

    # -----------------------------------------
    # Positive interaction
    # -----------------------------------------

    positive_phrases = [
        "thank you",
        "thanks",
        "please",
        "i appreciate",
        "are you okay",
        "you okay",
        "i care about you",
        "i'm glad",
        "im glad"
    ]

    for phrase in positive_phrases:

        if phrase in lower:
            trust += 1
            friendship += 1
            mood += 1

    # -----------------------------------------
    # Negative interaction
    # -----------------------------------------

    negative_phrases = [
        "shut up",
        "you're stupid",
        "you are stupid",
        "you're annoying",
        "you are annoying",
        "i hate you",
        "go away"
    ]

    for phrase in negative_phrases:

        if phrase in lower:
            trust -= 3
            friendship -= 2
            love -= 1
            mood -= 3

    # -----------------------------------------
    # Affection
    # -----------------------------------------

    if (
        "cute" in lower
        or "pretty" in lower
        or "beautiful" in lower
    ):
        love += 0.5

    if (
        "i love you" in lower
        or "love you" in lower
    ):
        love += 1
        trust += 0.5
        mood += 1

    return {
        "trust": round(clamp(trust), 2),
        "friendship": round(clamp(friendship), 2),
        "love": round(clamp(love), 2),
        "mood": round(clamp(mood), 2)
    }


# ============================================================
# PROMPT
# ============================================================

def build_prompt(
    message,
    memories,
    conversation,
    relationship,
    scene
):

    actions = get_actions(message)

    if actions:

        action_text = "\n".join(
            "- " + action.strip()
            for action in actions
            if action.strip()
        )

    else:

        action_text = (
            "No explicit physical action was written."
        )

    return f"""
CURRENT SCENE
=============

Location:
{scene.get("location", DEFAULT_SCENE["location"])}

Time:
{scene.get("time", DEFAULT_SCENE["time"])}

Weather:
{scene.get("weather", DEFAULT_SCENE["weather"])}

Nora:
{scene.get("nora_position", "")}

Player:
{scene.get("player_position", "")}

Scene:
{scene.get("description", "")}


RELATIONSHIP
============

Trust:
{relationship["trust"]}/100

Friendship:
{relationship["friendship"]}/100

Love toward player:
{relationship["love"]}/100

Mood:
{relationship["mood"]}/100


MEMORIES
========

{format_memories(memories)}


RECENT CONVERSATION
===================

{format_conversation(conversation)}


PLAYER'S CURRENT MESSAGE
========================

{message}


PLAYER'S VISIBLE ACTIONS
========================

{action_text}


INSTRUCTIONS
============

Respond as Nora.

The most important thing is to respond to the player's
CURRENT message.

React to the specific words and actions.

Do not give a generic response.

Do not pretend the player said something they did not say.

Do not ignore physical actions.

Do not read the player's mind.

Maintain continuity with the recent conversation.

Use memories only when they are relevant.

Let Nora have her own opinions.

Let Nora disagree when it makes sense.

Let Nora sometimes initiate conversation.

Do not end every response with a question.

Do not force romance.

Do not automatically increase romantic feelings simply
because the player is nice.

Make Nora feel like an actual character.

Return ONLY Nora's response.
"""


# ============================================================
# AI RESPONSE
# ============================================================

def ask_ai(prompt):

    if client is None:
        return None

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "system",
                    "content": NORA_PERSONALITY
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.85,

            max_tokens=700
        )

        answer = (
            response
            .choices[0]
            .message
            .content
        )

        if not answer:
            return None

        return answer.strip()

    except Exception as error:

        print(
            "AI ERROR:",
            repr(error)
        )

        return None


# ============================================================
# FALLBACK
# ============================================================

def fallback(message, relationship):

    actions = get_actions(message)

    lowered_actions = [
        x.lower()
        for x in actions
    ]

    if any(
        "walk away" in x
        or "leave" in x
        for x in lowered_actions
    ):

        return {
            "reply": (
                "Nora watches you start to leave. "
                "For a second she doesn't say anything, "
                "like she's trying to decide whether to "
                "let you go.\n\n"
                "\"Wait...\" she says quietly. "
                "\"You don't have to leave.\""
            ),
            "action":
                "*Nora steps closer to the doorway.*"
        }

    if any(
        "look away" in x
        or "look down" in x
        for x in lowered_actions
    ):

        return {
            "reply": (
                "Nora notices you avoiding her gaze. "
                "She doesn't immediately say anything. "
                "Instead, she gives you a moment.\n\n"
                "\"You don't have to be nervous around me,\" "
                "she says softly."
            ),
            "action":
                "*Nora tilts her head slightly.*"
        }

    if any(
        "smile" in x
        for x in lowered_actions
    ):

        return {
            "reply": (
                "Nora notices the smile on your face. "
                "A small smile appears on hers too before "
                "she seems to realize she's doing it.\n\n"
                "\"What?\" she says, trying not to smile."
            ),
            "action":
                "*Nora looks away for a second.*"
        }

    if any(
        "sit" in x
        for x in lowered_actions
    ):

        return {
            "reply": (
                "Nora watches you sit down. She seems "
                "slightly surprised that you're actually "
                "staying.\n\n"
                "\"I guess you're comfortable here now,\" "
                "she says."
            ),
            "action":
                "*Nora leans against the doorframe.*"
        }

    return {
        "reply": (
            "Nora listens carefully. She pauses for a "
            "moment before responding.\n\n"
            "\"I think I understand what you mean.\""
        ),
        "action":
            "*Nora studies your expression.*"
    }


# ============================================================
# CHAT
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json(
            silent=True
        )

        if not isinstance(data, dict):
            data = {}

        message = clean_text(
            data.get("message", ""),
            5000
        ).strip()

        if not message:

            return jsonify({
                "reply":
                    "Nora waits quietly.",
                "action":
                    "*Nora looks at you, waiting.*",
                "relationship":
                    {
                        "trust": 5,
                        "friendship": 0,
                        "love": 0,
                        "mood": 40
                    }
            })


        memories = data.get(
            "memories",
            []
        )

        conversation = data.get(
            "conversation",
            []
        )

        relationship = data.get(
            "relationship",
            {}
        )

        scene = data.get(
            "scene",
            DEFAULT_SCENE
        )

        if not isinstance(scene, dict):
            scene = DEFAULT_SCENE


        # -----------------------------------------
        # Calculate updated relationship.
        # -----------------------------------------

        new_relationship = (
            calculate_relationship(
                message,
                relationship
            )
        )


        # -----------------------------------------
        # Build AI context.
        # -----------------------------------------

        prompt = build_prompt(

            message,

            memories,

            conversation,

            new_relationship,

            scene

        )


        # -----------------------------------------
        # Ask AI.
        # -----------------------------------------

        reply = ask_ai(prompt)


        # -----------------------------------------
        # Fallback if AI unavailable.
        # -----------------------------------------

        if reply:

            action = ""

        else:

            result = fallback(
                message,
                new_relationship
            )

            reply = result["reply"]

            action = result["action"]


        # -----------------------------------------
        # Send result to browser.
        # -----------------------------------------

        return jsonify({

            "reply": reply,

            "action": action,

            "relationship":
                new_relationship

        })


    except Exception as error:

        print(
            "SERVER ERROR:",
            repr(error)
        )

        return jsonify({

            "reply":
                "Nora pauses for a moment. "
                "Something seems to have gone wrong.",

            "action":
                "*Nora looks around, confused.*",

            "relationship":
                {
                    "trust": 5,
                    "friendship": 0,
                    "love": 0,
                    "mood": 40
                }

        }), 500


# ============================================================
# INDEX
# ============================================================

@app.route("/")
def home():

    return send_from_directory(
        ".",
        "index.html"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
