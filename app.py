######## these stuffs ########
from flask import Flask, jsonify, request, render_template
import numpy as np
import json
import re

######## agents stuffs ########
from gameState import GameState
from agent import HumanWeb, Random, Minimax
from reinforcementAgent import ScoringAgent

human = HumanWeb()
random = Random()
minimax = Minimax()
reinforcement = ScoringAgent(tau_move=0.2, tau_wall=0.2)
    # def __init__(self, path="version_3.pth", losses_path="losses.txt", lr=1e-3, batch_size=2**8, gamma=0.99, memory_size=100_000, delay=0, tau=1.5, tau_move=0.2, tau_wall=1.5):

models = {
        "human": human,
        "random": random,
        "minimax": minimax,
        "reinforcement": reinforcement,
        }

app = Flask(__name__, static_folder="static", template_folder="templates")


def parse_state(payload):
    """JSON -> GameState"""
    return GameState(
        np.array(payload["walls"], dtype=bool),
        np.array(payload["agents"], dtype=np.int32),
        int(payload["turn"]),
    )

def to_jsonable(state: GameState):
    """GameState -> JSON (dict)"""
    return json.loads(state.toSerial())

def apply_action(state: GameState, action: dict):
    """
    Apply {type: 'move'|'wall', row:int, col:int, orientation?:0|1} to state.
    Returns (new_state, error_str_or_None).
    """
    if action is None:
        return state, None

    t = action.get("type")

    if t == "move":
        row, col = int(action["row"]), int(action["col"])
        legal = state.possibleMoves()
        if [row, col] not in legal:
            return None, "Illegal move"
        state.agents[state.turn, 0] = row
        state.agents[state.turn, 1] = col
        state.passTurn()
        return state, None

    if t == "wall":
        orientation = int(action["orientation"])  # 0=vertical, 1=horizontal
        row, col = int(action["row"]), int(action["col"])
        if state.agents[state.turn, 2] <= 0:
            return None, "No walls remaining"
        if not state.checkWall(orientation, row, col):
            return None, "Illegal wall placement"
        state.walls[orientation, row, col] = True
        state.agents[state.turn, 2] -= 1
        state.passTurn()
        return state, None

    return None, "Unknown action type"

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/api/newgame")
def newgame():
    s = GameState.newGame()
    return jsonify({"ok": True, "state": to_jsonable(s)})


## frontend prepares the command in a format the backend recognizes
## ie. one of "flip" "mirror" or something the regex "[vhm][0-8][0-8]" can recognize
## this function sends it to HumanWeb and catches possible exceptions
## and sends them to the frontend if so
## otherwise, sends the new gamestate to frontend to paint
@app.post("/api/human_step")
def human_step():
    """
    Frontend sends:
      {
        "state": { "walls": [[...],[...]], "agents":[[...],[...]], "turn": 0|1 },
        "command": "flip" | "mirror" | "[vhm][0-8][0-8]"
      }

    We reconstruct a GameState, pass it + command to HumanWeb.shoot,
    catch errors, and respond with the new state.
    """
    try:
        data = request.get_json(force=True) or {}
        if "state" not in data or "command" not in data:
            return jsonify(ok=False, error="Missing 'state' or 'command'"), 400

        # Accept either the dict shape or a serialized string.
        state_in = data["state"]
        if isinstance(state_in, str):
            state = GameState.fromSerial(state_in)
        else:
            # Expecting dict with walls/agents/turn
            walls = np.array(state_in["walls"], dtype=bool)
            agents = np.array(state_in["agents"], dtype=int)
            turn = int(state_in["turn"])
            state = GameState(walls, agents, turn)

        command = str(data["command"])

        # Validate command format early (optional but nice):
        if command not in ("flip", "mirror"):
            if not re.fullmatch(r"[vhm][0-8][0-8]", command):
                return jsonify(ok=False, error="Bad command format"), 400

        try:
            new_state = human.shoot(state, command)
        except ValueError as e:
            # Illegal action (wall placement, move, no walls, etc.)
            return jsonify(ok=False, error=str(e)), 400

        # Return the updated state as a plain JSON object (not a string)
        return jsonify(ok=True, state=json.loads(new_state.toSerial()))
    except Exception as e:
        # Catch-all
        return jsonify(ok=False, error=f"Server error: {e}"), 500


@app.post("/api/step")
def step():
    """
    Frontend sends:
      {
        "state": { "walls": [[...],[...]], "agents":[[...],[...]], "turn": 0|1 },
        "model": "random" | "minimax" | "reinforcement"
      }

    We reconstruct a GameState, and have the indicated model shoot it
    catch errors, and respond with the new state.
    """
    try:
        data = request.get_json(force=True) or {}
        if "state" not in data or "model" not in data:
            return jsonify(ok=False, error="Missing 'state' or 'model'"), 400

        # Accept either the dict shape or a serialized string.
        state_in = data["state"]
        if isinstance(state_in, str):
            state = GameState.fromSerial(state_in)
        else:
            # Expecting dict with walls/agents/turn
            walls = np.array(state_in["walls"], dtype=bool)
            agents = np.array(state_in["agents"], dtype=int)
            turn = int(state_in["turn"])
            state = GameState(walls, agents, turn)
        model = str(data["model"])
        new_state = models[model].shoot(state)
        if new_state is None:
            return jsonify(ok=False, error=f"{model_name} did not return a move"), 500
        print(new_state)
        return jsonify(ok=True, state=json.loads(new_state.toSerial()))
    except Exception as e:
        # Catch-all
        return jsonify(ok=False, error=f"Server error: {e}"), 500

## TODO: print functionality that prints the board as a json

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")


