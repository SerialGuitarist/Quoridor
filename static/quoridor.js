console.log('JavaScript Online');
console.log('Quoridor Version 0.1');

var gameCanvas = document.getElementById('gameCanvas');
var topPlayer = document.getElementById('topPlayer');
var bottomPlayer = document.getElementById('bottomPlayer');
var newGameButton = document.getElementById('newGameButton');
// var pauseGameButton = document.getElementById('pauseGameButton');
// var resumeGameButton = document.getElementById('resumeGameButton');
// var scoreCounter = document.getElementById('scoreCounter');

var ctx = gameCanvas.getContext('2d');
var topCtx = topPlayer.getContext('2d');
var bottomCtx = bottomPlayer.getContext('2d');

var state;

newGameButton.onclick = newGame;

async function newGame() {
	try {
		const response = await fetch('/newgame', {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json'
			}
		});
		if (response.ok) {
			const state = await response.json();
			gameStateToBoard(state);
		} else {
			console.error('Failed to fetch game state');
		}
	} catch (error) {
		console.error('Error:', error);
	}
}

/*
pauseGameButton.onclick = function() {
    pauseGameButton.style.display = 'none';
    resumeGameButton.style.display = 'inline';
}

resumeGameButton.onclick = function() {
    pauseGameButton.style.display = 'inline';
    resumeGameButton.style.display = 'none';
}
*/

const dim = {
    boardSide: 830,
    playerHeight: 75,
    playerRad: 30,
    wallLong: 160,
    wallShort: 20,
    blockSide: 70,
    space: 20,
    fullSpace: 90
}

const color = {
    white: 'gold',
    black: 'brown',
    block: 'gray',
    background: '#654321', //brown
    wall: 'orange'
}

var whitePlayer, blackPlayer;

function gameStateToBoard(state) {
    ////initializing the main game board////
    ctx.fillStyle = color.background;
    ctx.fillRect(0,0,830,830);
    ctx.fillStyle = color.block;
    for(let row = 0; row < 9; row++) {for(let col = 0; col < 9; col++) {
        ctx.fillRect(dim.space*(col+1) + col*dim.blockSide, dim.space*(row+1) + row*dim.blockSide, dim.blockSide, dim.blockSide);
    }}
    ////////////////////////////////////////

    ////top white (turn 1) player walls////
    topCtx.fillStyle = color.block;
    topCtx.fillRect(0,0,dim.boardSide,dim.playerHeight);
    for(let wall = 0; wall < 10; wall++) {
        topCtx.fillStyle = color.background;
        topCtx.fillRect(wall*dim.fullSpace,0,dim.space,dim.playerHeight);
    }
    for(let wall = 0; wall < state.agents[1][2]; wall++) {
        topCtx.fillStyle = color.wall;
        topCtx.fillRect(wall*dim.fullSpace,0,dim.space,dim.playerHeight);
    }
    /////////////////////////

    ////bottom black (turn 0) player walls////
    bottomCtx.fillStyle = color.block;
    bottomCtx.fillRect(0,0,dim.boardSide,dim.playerHeight);
    for(let wall = 0; wall < 10; wall++) {
        bottomCtx.fillStyle = color.background;
        bottomCtx.fillRect(wall*dim.fullSpace,0,dim.space,dim.playerHeight);
    }
    for(let wall = 0; wall < state.agents[0][2]; wall++) {
        bottomCtx.fillStyle = color.wall;
        bottomCtx.fillRect(wall*dim.fullSpace,0,dim.space,dim.playerHeight);
    }
    /////////////////////////

    ////top player////
	placePawn(state.agents[1][1], state.agents[1][0], true)
    //////////////////

    ////bottom player////
	placePawn(state.agents[0][1], state.agents[0][0], false)
    /////////////////////


    //// walls ////
	for (i in ["ver", "hor"]) {
		for (row in state.walls[i]) {
			for (col in state.walls[i][row]) {
				if (state.walls[i][row][col]) {
					placeWall(i, col, row);
				}
			}
		}
	}
    /////////////////////


	console.log(state)
}

function fillBlock(col, row, blockColor = color.block) {
    ctx.beginPath();
    ctx.fillStyle = blockColor;
    ctx.fillRect(dim.space + dim.fullSpace*col, dim.space + dim.fullSpace*row, dim.blockSide, dim.blockSide);
}

function placeWall(hor, col, row) {
    ctx.beginPath();
	////adding a wall////
	ctx.fillStyle = color.wall;
	if(hor == 1) {
		ctx.fillRect(dim.space+dim.fullSpace*col,dim.fullSpace+dim.fullSpace*row, dim.wallLong, dim.wallShort);
	} else {
		ctx.fillRect(dim.fullSpace+dim.fullSpace*col,dim.space+dim.fullSpace*row, dim.wallShort, dim.wallLong);
	}
}

function placePawn(col, row, white) {
    ctx.beginPath();
    if(white) {
        ctx.fillStyle = color.white;
    } else {
        ctx.fillStyle = color.black;
    }
    ctx.arc(dim.space+dim.fullSpace*col+dim.blockSide/2, dim.space+dim.fullSpace*row+dim.blockSide/2, dim.playerRad,0,2*Math.PI);
    ctx.fill();
}

function highlightBlocks(blocks, highlight) {
    for(let block of blocks) {
        fillBlock(block.col, block.row, highlight? 'white': color.block);
    }
}

//// mouse related functionality ////
gameCanvas.onclick = function(e) {
    let pos = getMousePosition(e);
    let col = Math.floor(pos.x / dim.fullSpace);
    let row = Math.floor(pos.y / dim.fullSpace);
    let xMod = pos.x % dim.fullSpace;
    let yMod = pos.y % dim.fullSpace;

    // let player = playerWaiting == 1 ? whitePlayer : blackPlayer;
    // let white = playerWaiting == 1 ? true : false;

    if(xMod >= 20 && yMod >= 20) {
        // console.log('block:',col, row);
        // setPlayer(col,row,false);
        if(checkMovement(white, col, row)) {
            player.promiseResolve({type:0, col:col, row:row});
        };
    } else if (xMod < 20 && yMod >= 20 && col > 0 && col < 9 && row < 8) {
        // console.log('vertical wall:',col - 1, row);
        if(checkWall(false,col - 1,row) && player.walls > 0) {
            player.promiseResolve({type:1, col:col - 1, row:row});
        }
        // console.log(checkWall(false,col - 1,row));
    } else if (xMod >= 20 && yMod < 20 && row > 0 && row < 9 && col < 8) {
        // console.log(checkWall(true,col,row - 1));
        if(checkWall(true,col,row - 1)  && player.walls > 0) {
            player.promiseResolve({type:2, col:col, row:row-1})
        }
    }   
}

function getMousePosition(event) {
    let rect = gameCanvas.getBoundingClientRect();
    return {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top
    };
}


//// was once used to debug and label the nodes but not used anymore /////
function topLeft(col, row, text) {
    ctx.fillStyle = 'black';
    ctx.font = "15px Arial";
    ctx.fillText(text, dim.space + dim.fullSpace*col, dim.space * 2 + dim.fullSpace*row, dim.blockSide); 
}

function topRight(col, row, text) {
    ctx.fillStyle = 'green';
    ctx.font = "15px Arial";
    ctx.fillText(text, dim.space * 3 + dim.fullSpace*col, dim.space * 2 + dim.fullSpace*row, dim.blockSide); 
}

function bottomBottom(col, row, text) {
    ctx.fillStyle = 'purple';
    ctx.font = "25px Arial";
    ctx.fillText(text, dim.space * 2 + dim.fullSpace*col, dim.space * 4 + dim.fullSpace*row, dim.blockSide); 
}






