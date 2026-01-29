console.log("Quoridor frontend ready");

const gameCanvas  = document.getElementById("gameCanvas");
const topPlayer   = document.getElementById("topPlayer");
const bottomPlayer= document.getElementById("bottomPlayer");
const newGameBtn  = document.getElementById("newGameButton");
const flipBtn  = document.getElementById("flipButton");
const mirrorBtn  = document.getElementById("mirrorButton");
const stepBtn  = document.getElementById("stepButton");
const statusEl    = document.getElementById("status");
const autoStep = document.getElementById("autoStep");

let whiteAgent = document.querySelector('input[name="white"]:checked').value;
let blackAgent = document.querySelector('input[name="black"]:checked').value;

// white player selectors
document.getElementById("selectWhiteHuman").onclick = () => { whiteAgent = "human"; };
document.getElementById("selectWhiteRandom").onclick = () => { whiteAgent = "random"; };
document.getElementById("selectWhiteMinimax").onclick = () => { whiteAgent = "minimax"; };
document.getElementById("selectWhiteReinforcement").onclick = () => { whiteAgent = "reinforcement"; };

// black player selectors
document.getElementById("selectBlackHuman").onclick = () => { blackAgent = "human"; };
document.getElementById("selectBlackRandom").onclick = () => { blackAgent = "random"; };
document.getElementById("selectBlackMinimax").onclick = () => { blackAgent = "minimax"; };
document.getElementById("selectBlackReinforcement").onclick = () => { blackAgent = "reinforcement"; };


// canvas shenanigans
const ctx      = gameCanvas.getContext("2d");
const topCtx   = topPlayer.getContext("2d");
const bottomCtx= bottomPlayer.getContext("2d");

const dim = {
	boardSide: 830,
	playerHeight: 75,
	playerRad: 30,
	wallLong: 160,
	wallShort: 20,
	blockSide: 70,
	space: 20,
	fullSpace: 90,
};

const color = {
	white: "gold",
	black: "brown",
	block: "gray",
	background: "#654321",
	wall: "orange",
};

let state = null;

// helpers for controls
const whiteIsHuman = () => document.getElementById("selectWhiteHuman").checked;
const blackIsHuman = () => document.getElementById("selectBlackHuman").checked;
const isHumanTurn = (s) => (s.turn === 1 ? whiteIsHuman() : blackIsHuman());

function isGameOver(s) {
	return s.agents[0][0] === 0 || s.agents[1][0] === 8;
}

// ================== Drawing ==================
function drawState(s) {
	// board background
	ctx.fillStyle = color.background;
	ctx.fillRect(0, 0, dim.boardSide, dim.boardSide);

	// tiles
	ctx.fillStyle = color.block;
	for (let r = 0; r < 9; r++) {
		for (let c = 0; c < 9; c++) {
			ctx.fillRect(
				dim.space * (c + 1) + c * dim.blockSide,
				dim.space * (r + 1) + r * dim.blockSide,
				dim.blockSide,
				dim.blockSide
			);
		}
	}

	// top (white) walls bar
	topCtx.fillStyle = color.block;
	topCtx.fillRect(0, 0, dim.boardSide, dim.playerHeight);
	for (let i = 0; i < 10; i++) {
		topCtx.fillStyle = color.background;
		topCtx.fillRect(i * dim.fullSpace, 0, dim.space, dim.playerHeight);
	}
	for (let i = 0; i < s.agents[1][2]; i++) {
		topCtx.fillStyle = color.wall;
		topCtx.fillRect(i * dim.fullSpace, 0, dim.space, dim.playerHeight);
	}

	// bottom (black) walls bar
	bottomCtx.fillStyle = color.block;
	bottomCtx.fillRect(0, 0, dim.boardSide, dim.playerHeight);
	for (let i = 0; i < 10; i++) {
		bottomCtx.fillStyle = color.background;
		bottomCtx.fillRect(i * dim.fullSpace, 0, dim.space, dim.playerHeight);
	}
	for (let i = 0; i < s.agents[0][2]; i++) {
		bottomCtx.fillStyle = color.wall;
		bottomCtx.fillRect(i * dim.fullSpace, 0, dim.space, dim.playerHeight);
	}

	// walls
	for (let r = 0; r < 8; r++) {
		for (let c = 0; c < 8; c++) {
			if (s.walls[1][r][c]) placeWall(1, c, r); // horizontal
			if (s.walls[0][r][c]) placeWall(0, c, r); // vertical
		}
	}

	// pawns
	placePawn(s.agents[1][1], s.agents[1][0], true);  // white (top)
	placePawn(s.agents[0][1], s.agents[0][0], false); // black (bottom)

	updateStatus(s);
	state = s;
	console.log(s);
}

function placeWall(orientation, col, row) {
	ctx.beginPath();
	ctx.fillStyle = color.wall;
	if (orientation === 1) {
		ctx.fillRect(dim.space + dim.fullSpace * col, dim.fullSpace + dim.fullSpace * row, dim.wallLong, dim.wallShort);
	} else {
		ctx.fillRect(dim.fullSpace + dim.fullSpace * col, dim.space + dim.fullSpace * row, dim.wallShort, dim.wallLong);
	}
}

function placePawn(col, row, white) {
	ctx.beginPath();
	ctx.fillStyle = white ? color.white : color.black;
	ctx.arc(
		dim.space + dim.fullSpace * col + dim.blockSide / 2,
		dim.space + dim.fullSpace * row + dim.blockSide / 2,
		dim.playerRad, 0, 2 * Math.PI
	);
	ctx.fill();
}

function updateStatus(s) {
	if (isGameOver(s)) {
		const winner = s.agents[0][0] === 0 ? "Black" : "White";
		statusEl.textContent = `Game over: ${winner} wins.`;
	} else {
		statusEl.textContent = s.turn === 1 ? "White to move" : "Black to move";
	}
}

// ================== Click -> Action ==================
gameCanvas.onclick = async (e) => {
	if (!state || !isHumanTurn(state) || isGameOver(state)) return;

	const { col, row, xMod, yMod } = getBoardClick(e);

	// Build compact command string that backend expects:
	// - move: "m<row><col>"
	// - vertical wall: "v<row><col>"
	// - horizontal wall: "h<row><col>"
	let command = null;

	if (xMod >= 20 && yMod >= 20) {
		// Clicked inside a block => move
		command = `m${row}${col}`;
	} else if (xMod < 20 && yMod >= 20 && col > 0 && col < 9 && row < 8) {
		// Left gutter => vertical wall at (row, col-1)
		command = `v${row}${col - 1}`;
	} else if (xMod >= 20 && yMod < 20 && row > 0 && row < 9 && col < 8) {
		// Top gutter => horizontal wall at (row-1, col)
		command = `h${row - 1}${col}`;
	}

	if (!command) return;

	statusEl.textContent = ""; // clear any old error

	try {
		const res = await fetch("/api/human_step", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ state, command }),
		});

		const data = await res.json();
		if (!res.ok || !data.ok) {
			statusEl.textContent = data.error || "Illegal action";
			return;
		}

		drawState(data.state);
		if (autoStep.checked) {
			stepBtnFunction(e);
		}
	} catch (err) {
		statusEl.textContent = "Network error";
		console.error(err);
	}
};

flipBtn.onclick = async (e) => {
	if (!state) return;
	statusEl.textContent = "";
	command = "flip"
	try {
		const res = await fetch("/api/human_step", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ state, command }),
		});
		const data = await res.json();
		drawState(data.state);
	} catch (err) {
		statusEl.textContent = "Network error";
		console.error(err);
	}
};

mirrorBtn.onclick = async (e) => {
	if (!state) return;
	statusEl.textContent = "";
	command = "mirror"
	try {
		const res = await fetch("/api/human_step", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ state, command }),
		});
		const data = await res.json();
		drawState(data.state);
	} catch (err) {
		statusEl.textContent = "Error. Check console";
		console.error(err);
	}
};

async function stepBtnFunction(e) {
	if (!state || isHumanTurn(state) || isGameOver(state)) return;
	statusEl.textContent = "";
	// console.log(document.querySelector('input[name="white"]:checked').value);
	model = state.turn ? whiteAgent : blackAgent;
	try {
		const res = await fetch("/api/step", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ state, model }),
		});
		const data = await res.json();
		console.log(data);
		drawState(data.state);
	} catch (err) {
		statusEl.textContent = "Error in step button. Check console";
		console.error(err);
	}
	if (autoStep.checked) {
		stepBtnFunction(e);
	}
};

stepBtn.onclick = stepBtnFunction;

// Build compact command string that backend expects:
// - move: "m<row><col>"
// - vertical wall: "v<row><col>"
function getBoardClick(event) {
	const rect = gameCanvas.getBoundingClientRect();
	const x = event.clientX - rect.left;
	const y = event.clientY - rect.top;
	const col = Math.floor(x / dim.fullSpace);
	const row = Math.floor(y / dim.fullSpace);
	const xMod = x % dim.fullSpace;
	const yMod = y % dim.fullSpace;
	return { col, row, xMod, yMod };
}

// ================== Game flow ==================
newGameBtn.onclick = async () => {
	statusEl.textContent = "";
	const resp = await fetch("/api/newgame");
	const data = await resp.json();
	if (!resp.ok || !data.ok) {
		statusEl.textContent = data.error || "Failed to start new game";
		return;
	}
	drawState(data.state); // drawState will set the global `state`
};

async function maybeAutoAI() {
	while (!isHumanTurn(state) && !isGameOver(state)) {
		const res = await fetch("/api/ai", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ state }),
		});
		const data = await res.json();
		if (!data.ok) break;
		state = data.state;
		drawState(state);
		if (data.done) break;
	}
}

// Boot
(async function init() {
	const resp = await fetch("/api/newgame");
	const data = await resp.json();
	if (!resp.ok || !data.ok) {
		statusEl.textContent = data.error || "Failed to start new game";
		return;
	}
	drawState(data.state);
})();


