from flask import Flask
from flask import render_template
from flask import url_for
from flask import jsonify
from flask import session

import numpy as np
import heapq
from collections import deque
from gameState import GameState

app = Flask(__name__)
app.secret_key = 'snowballsnowballsnowballsnowball'

@app.route("/")
def index():
    # return "Hello, world!"
    return render_template("Quoridor.html")

@app.route("/newgame", methods=['GET'])
def newgame():
    ## return jsonify(jsonState)
    session['state'] = GameState.newGame().toSerial()
    # return jsonify(message=1)
    return jsonify(session['state'])



if __name__ == "__main__":
    app.run(debug=True)
