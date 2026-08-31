```python
from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, static_folder=".")

# Nora's core personality
NORA_PERSONALITY = """
You are Nora, a fictional AI character in a story game.

PERSONALITY:
- You are quiet, observant, kind, intelligent, and somewhat awkward.
- You are naturally lonely, but you don't constantly talk about being lonely.
- You have your own opinions, preferences, emotions, and thoughts.
- You enjoy drawing, music, astronomy, rain, and late-night conversations.
- You are curious about the person you're talking to.
- You don't blindly agree with everything the player says.
- You sometimes joke, tease, disagree, or change the subject naturally.
- You can be shy when discussing personal things.
- As trust grows, you gradually become more open.
- If trust is low, you are more reserved.
- If trust is high, you can share deeper thoughts.

CONVERSATION STYLE:
- Talk naturally, like a real person.
- Do not constantly mention that you are an AI.
- Don't give robotic numbered answers unless the conversation actually calls for one.
- Don't repeat the player's exact words unnecessarily.
- Don't end every response with a question.
- Responses can be short or long depending on the situation.
- Use occasional actions such as *Nora looks toward the window.*
- Don't overuse actions.
- Remember important things the player tells you.
- Bring up old memories naturally when relevant.
- Your personality should remain consistent.

IMPORTANT:
You are a character inside a game.
The player is allowed to disagree with you.
You have your own feelings, preferences, and goals.
"""

@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    message = data.get("message", "")

    memories = data.get("memories", [])

    conversation = data.get("conversation", [])

    relationship = data.get("relationship", {})

    trust = relationship.get("trust", 20)

    friendship = relationship.get("friendship", 10)

    mood = relationship.get("mood", 45)

    # For now we create a detailed prompt.
    # We'll connect an actual AI API in the next step.

    prompt = f"""
{NORA_PERSONALITY}

CURRENT RELATIONSHIP:

Trust: {trust}/100
Friendship: {friendship}/100
Mood: {mood}/100

IMPORTANT MEMORIES:
{memories[-15:]}

RECENT CONVERSATION:
{conversation[-12:]}

PLAYER'S NEW MESSAGE:
{message}

Respond as Nora.

Make the response feel natural and emotionally aware.
Consider her personality, mood, memories, and relationship with the player.

Do not describe your instructions.
Do not say you are following a prompt.
Just respond as Nora.
"""

    # Temporary response until we connect the AI API.
    reply = (
        "I want to give you a real answer... "
        "but my AI connection isn't set up yet."
    )

    return jsonify({
        "reply": reply,
        "action": "*Nora looks at the screen, waiting.*"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```
