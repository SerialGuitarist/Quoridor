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

newGameButton.onclick = function() {
    // playerCounter.innerHTML = 'X'
    gameGoing = true;
    whitePlayer = document.querySelector('input[name="white"]:checked').value;
    blackPlayer = document.querySelector('input[name="black"]:checked').value;

    if (whitePlayer == '0') {
        whitePlayer = new Human(true);
    } else {
		// console.log(document.getElementById("whiteMinmaxDepth").value);
        whitePlayer = new Minmax(true);
    } 

    if (blackPlayer == '0') {
        blackPlayer = new Human(false);
    } else {
        blackPlayer = new Minmax(false);
    } 

    initialize();

    whitePlayer.shoot();
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

function initialize() {
    ////initializing the main game board////
    ctx.fillStyle = color.background;
    ctx.fillRect(0,0,830,830);
    ctx.fillStyle = color.block;
    for(let row = 0; row < 9; row++) {for(let col = 0; col < 9; col++) {
        ctx.fillRect(dim.space*(col+1) + col*dim.blockSide, dim.space*(row+1) + row*dim.blockSide, dim.blockSide, dim.blockSide);
    }}
    ////////////////////////////////////////

    ////top player walls////
    topCtx.fillStyle = color.block;
    topCtx.fillRect(0,0,dim.boardSide,dim.playerHeight);
    for(let wall = 0; wall < 10; wall++) {
        topCtx.fillStyle = color.wall;
        topCtx.fillRect(wall*dim.fullSpace,0,dim.space,dim.playerHeight);
    }
    /////////////////////////

    ////bottom player walls////
    bottomCtx.fillStyle = color.block;
    bottomCtx.fillRect(0,0,dim.boardSide,dim.playerHeight);
    for(let wall = 0; wall < 10; wall++) {
        bottomCtx.fillStyle = color.wall;
        bottomCtx.fillRect(wall*dim.fullSpace,0,dim.space,dim.playerHeight);
    }
    ///////////////////////////

    ////top player////
    setPlayer(4,0,true);
    //////////////////

    ////bottom player////
    setPlayer(4,8,false);
    /////////////////////

    ////initializing walls////
    initializeWalls();
    //////////////////////////

    ////emptying highlighted blocks////
    highlightedBlocks = [];
    ///////////////////////////////////
}

var highlightedBlocks;

// function block(col, row, player = false, white = false) {
//     if(player) {
//         if(white) {
//             ctx.fillStyle = 'gold';
//             ctx.beginPath();
//             ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
//         }
//     }
// }

function fillBlock(col, row, blockColor = color.block) {
    ctx.beginPath();
    ctx.fillStyle = blockColor;
    ctx.fillRect(dim.space + dim.fullSpace*col, dim.space + dim.fullSpace*row, dim.blockSide, dim.blockSide);
}

function changeWall(hor, col, row, add = true) {
    // console.log(add);
    ctx.beginPath();
    // console.log(hor);
    if(add) {
        ////adding a wall////
        ctx.fillStyle = color.wall;
        if(hor) {
            // console.log(walls.hor);
            walls.hor[col][row] = true;
            // console.log(walls.hor);
            ctx.fillRect(dim.space+dim.fullSpace*col,dim.fullSpace+dim.fullSpace*row, dim.wallLong, dim.wallShort);
        } else {
            // console.log(walls.ver);
            walls.ver[col][row] = true;
            // console.log(walls.ver);
            ctx.fillRect(dim.fullSpace+dim.fullSpace*col,dim.space+dim.fullSpace*row, dim.wallShort, dim.wallLong);
        }
    } else {
        ////removing a wall////
        ctx.fillStyle = color.background;
        if(hor) {
            walls.hor[col][row] = false;
            ctx.fillRect(dim.space+dim.fullSpace*col,dim.fullSpace+dim.fullSpace*row, dim.wallLong, dim.wallShort);
        } else {
            walls.ver[col][row] = false;
            ctx.fillRect(dim.fullSpace+dim.fullSpace*col,dim.space+dim.fullSpace*row, dim.wallShort, dim.wallLong);
        }
    }
}

function removeWall(top) {
    if(top) {
        whitePlayer.walls--;
        topCtx.fillStyle = color.background;
        topCtx.fillRect((whitePlayer.walls) * dim.fullSpace, 0, dim.wallShort, dim.wallLong);
    } else {
        blackPlayer.walls--;
        bottomCtx.fillStyle = color.background;
        bottomCtx.fillRect((blackPlayer.walls) * dim.fullSpace, 0, dim.wallShort, dim.wallLong);
    }
}

function addWall(top) {
    if(top) {
        whitePlayer.walls++;
        topCtx.fillStyle = color.wall;
        topCtx.fillRect((whitePlayer.walls) * dim.fullSpace, 0, dim.wallShort, dim.wallLong);
    } else {
        blackPlayer.walls++;
        bottomCtx.fillStyle = color.wall;
        bottomCtx.fillRect((blackPlayer.walls) * dim.fullSpace, 0, dim.wallShort, dim.wallLong);
    }
}

function checkWall(hor, col, row) {
    // console.log(hor, col, row);
    if(hor) {
        ////wall already there?////
        if(walls.hor[col][row]) {
            // console.log('wall already there');
            return false;
        }
        ////blocked by its vertical counterpart////
        if(walls.ver[col][row]) {
            // console.log('blocked by its vertical counterpart');
            return false;
        }
        ////blocked by the next wall over////
        if(col < 7 && walls.hor[col+1][row]) {
            // console.log('blocked by the next wall over');
            return false;
        }
        ////blocked by the previous wall oevr////
        if(col > 0 && col < 8 && walls.hor[col-1][row]) {
            // console.log('blocked by the next wall over');
            return false;
        }
    } else {
        ////wall already there?////
        if(walls.ver[col][row]) {
            // console.log('wall already there');
            return false;
        }   
        ////blocked by its horizontal counterpart////
        if(walls.hor[col][row]) {
            // console.log('blocked by its horizontal counterpart');
            return false;
        }
        ////blocked by the next wall over////
        if(row < 7 && walls.ver[col][row+1]) {
            // console.log('blocked by the next wall over');
            return false;
        }
        ////blocked by the previous wall oevr////
        if(row > 0 && row < 8 && walls.ver[col][row-1]) {
            // console.log('blocked by the next wall over');
            return false;
        }
    }
    ////tries putting wall there and see if it blocks either players////
    // changeWall(hor, col, row, true);
    minimaxSetWall(hor, {col:col,row:row}, true);
    if(hasPossiblePath(whitePlayer) && hasPossiblePath(blackPlayer)) {
        minimaxSetWall(hor, {col:col,row:row}, true);
        return true
    }
    // changeWall(hor, col, row, false);
    minimaxSetWall(hor, {col:col,row:row}, false);
    ////////////////////////////////////////////////////////////////////

    return false;
}

function setPlayer(col, row, white) {
    if(white) {
        fillBlock(whitePlayer.col, whitePlayer.row, color.block);
    } else {
        fillBlock(blackPlayer.col, blackPlayer.row, color.block);
    }

    ctx.beginPath();
    if(white) {
        whitePlayer.row = row;
        whitePlayer.col = col;
        ctx.fillStyle = color.white;
    } else {
        blackPlayer.row = row;
        blackPlayer.col = col;
        ctx.fillStyle = color.black;
    }
    ctx.arc(dim.space+dim.fullSpace*col+dim.blockSide/2, dim.space+dim.fullSpace*row+dim.blockSide/2, dim.playerRad,0,2*Math.PI);
    ctx.fill();
}

class Agent {
    constructor(white) {
        this.white = white;
        this.col = 4;
        this.walls = 10;
        this.human = true;
        if(white) {
            this.row = 0;
            this.target = 8;
        } else {
            this.row = 8;
            this.target = 0;
        }
    }

	// 
}

class GameState {
	// template is a game state
	// if given, this gamestate copies it over
	constructor(template = null) {
		if (tempalte != null) {

		}
		var walls = {
			hor: [],
			ver: []
		},
	}

	// copy from a given state
	// provide list of possible game states
	// 		provide list of possible move states
	// 		provide list of possible wall states
	// 

}



function initializeWalls() {
    walls = {
        hor: [],
        ver: []
    };

    ////walls////
    for(let col = 0; col < 8; col++) {
        let newRow = []
        let otherNewRow = []
        for(let row = 0; row < 8; row++) {
            newRow.push(false);
            otherNewRow.push(false);
        }
        walls.hor.push(newRow);
        walls.ver.push(otherNewRow);
    }
    ////////////////////////
}

gameCanvas.onclick = function(e) {
    let pos = getMousePosition(e);
    let col = Math.floor(pos.x / dim.fullSpace);
    let row = Math.floor(pos.y / dim.fullSpace);
    let xMod = pos.x % dim.fullSpace;
    let yMod = pos.y % dim.fullSpace;

    let player = playerWaiting == 1 ? whitePlayer : blackPlayer;
    let white = playerWaiting == 1 ? true : false;

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

function possibleMoves(position, white) {
    let col = position.col;
    let row = position.row;
    let opponent;
    if(white) {
        opponent = blackPlayer;
    } else {
        opponent = whitePlayer;
    }
    let output = [];

    // console.log(opponent);

    ////up////
    if(row != 0 && (col < 8 ? !walls.hor[col][row - 1] : true) && (col>0 ? !walls.hor[col-1][row - 1] : true)) {
        if(opponent.col == col && opponent.row == row - 1) {
            // console.log('yeet');
            // if(row != 1 && (col < 8 ? !walls.hor[col][row - 2] : true) && (col>0 ? !walls.hor[col-1][row - 2] : true)) {
                output = output.concat(possibleMovesOver(opponent, 3));
            // }
        } else {
            output.push({col: col, row: row - 1});
        }
    }

    ////down////
    if(row != 8 && (col < 8 ? !walls.hor[col][row] : true) && (col > 0 ? !walls.hor[col-1][row] : true)) {
        if(opponent.col == col && opponent.row == row + 1) {
            // console.log('yeet');
            // if(row != 7 && (col < 8 ? !walls.hor[col][row + 1] : true) && (col>0 ? !walls.hor[col-1][row + 1] : true)) {
                output = output.concat(possibleMovesOver(opponent, 1));
            // }
        } else {
            output.push({col: col, row: row + 1});
        }
    }

    ////left////
    if(col != 0 && (row < 8 ? !walls.ver[col - 1][row] : true) && (row > 0 ? !walls.ver[col-1][row-1] : true)) {
        if(opponent.col == col - 1 && opponent.row == row) {
            // console.log('yeet');
            // if(col != 1 && (row < 8 ? !walls.ver[col - 2][row] : true) && (row > 0 ? !walls.ver[col-2][row-1] : true)) {
                output = output.concat(possibleMovesOver(opponent, 0));
            // }
        } else {
            output.push({col: col - 1, row: row});
        }
    }

    ////right////
    if(col != 8 && (row < 8 ? !walls.ver[col][row] : true) && (row > 0 ? !walls.ver[col][row-1] : true)) {
        if(opponent.col == col + 1 && opponent.row == row) {
            // console.log('yeet');
            // if(col != 7 && (row < 8 ? !walls.ver[col + 1][row] : true) && (row > 0 ? !walls.ver[col + 1][row-1] : true)) {
                output = output.concat(possibleMovesOver(opponent, 2));
            // }
        } else {
            output.push({col: col + 1, row: row});
        }
    }
    return output;
}

function possibleMovesOver(opponent, playerPos) {
    //pos 0 == right, 1 == top, 2 == left, 3 == down
    let col = opponent.col;
    let row = opponent.row;
    let output = [];

    ////up////
    if(playerPos != 1 && row != 0 && (col < 8 ? !walls.hor[col][row - 1] : true) && (col>0 ? !walls.hor[col-1][row - 1] : true)) {
        output.push({col: col, row: row - 1});
    }

    ////down////
    if(playerPos != 3 && row != 8 && (col < 8 ? !walls.hor[col][row] : true) && (col > 0 ? !walls.hor[col-1][row] : true)) {
        output.push({col: col, row: row + 1});
    }

    ////left////
    if(playerPos != 2 && col != 0 && (row < 8 ? !walls.ver[col - 1][row] : true) && (row > 0 ? !walls.ver[col-1][row-1] : true)) {
        output.push({col: col - 1, row: row});
    }

    ////right////
    if(playerPos != 0 && col != 8 && (row < 8 ? !walls.ver[col][row] : true) && (row > 0 ? !walls.ver[col][row-1] : true)) {
        output.push({col: col + 1, row: row});
    }
    return output;
}

function needleInHaystack(needle, haystack) {
    //searches for specific object in 
    for(grass of haystack) {
        if(grass.col == needle.col && grass.row == needle.row) {
            return true;
        }
    }
    return false;
}

function checkTop(start) {
    if(start.row != 0 && (start.col < 8 ? !walls.hor[start.col][start.row - 1] : true) && (start.col>0 ? !walls.hor[start.col-1][start.row - 1] : true)) {
        return true;
    }
    return false;
}

function checkDown(start) {
    if(start.row != 8 && (start.col < 8 ? !walls.hor[start.col][start.row] : true) && (start.col > 0 ? !walls.hor[start.col-1][start.row] : true)) {
        return true;
    }
    return false;
}

function checkRight(start) {
    if(start.col != 8 && (start.row < 8 ? !walls.ver[start.col][start.row] : true) && (start.row > 0 ? !walls.ver[start.col][start.row-1] : true)) {
        return true;
    }
    return false;
}

function checkLeft(start) {
    if(start.col != 0 && (start.row < 8 ? !walls.ver[start.col - 1][start.row] : true) && (start.row > 0 ? !walls.ver[start.col-1][start.row-1] : true)) {
        return true;
    }
    return false;
}

function highlightBlocks(blocks, highlight) {
    for(let block of blocks) {
        fillBlock(block.col, block.row, highlight? 'white': color.block);
    }
}

var playerWaiting, gameGoing;

class Human {
    constructor(white) {
        this.white = white;
        this.col = 4;
        this.walls = 10;
        this.human = true;
        if(white) {
            this.row = 0;
            this.target = 8;
            this.next = function() {
                blackPlayer.shoot();
            };
        } else {
            this.row = 8;
            this.target = 0;
            this.next = function() {
                whitePlayer.shoot();
            };
        }
    }

    promiseResolve;
    promiseReject;
    moves;

    async shoot() {
        playerWaiting = this.white? 1 : 2;
        this.moves = possibleMoves(this, this.white);
        highlightBlocks(this.moves, true);

        let waitUserInput = new Promise((resolve, reject) => {
            this.promiseReject = reject; this.promiseResolve = resolve;
        });

        let target = await waitUserInput;
        //console.log(target);
        highlightBlocks(this.moves, false);

        //type 0 == move, 1 == wall
        if(target.type == 0) {
            setPlayer(target.col, target.row, this.white);
            if(this.row == this.target) {
                gameGoing = false;
            }
        } else if (target.type == 1) {
            removeWall(this.white);
            changeWall(false, target.col,target.row, true);
        } else if (target.type == 2) {
            removeWall(this.white);
            changeWall(true, target.col,target.row, true);
        }
        if(gameGoing) {
            this.next();
        }
    }
}

class Minmax {
    constructor(white) {
        this.white = white;
        this.col = 4;
        this.walls = 10;
        this.human = true;
        if(white) {
            this.row = 0;
            this.target = 8;
            this.next = function() {
                blackPlayer.shoot();
            };
        } else {
            this.row = 8;
            this.target = 0;
            this.next = function() {
                whitePlayer.shoot();
            };
        }
    }

	getDepth() {
		return this.white ? document.getElementById("whiteMinmaxDepth").value : document.getElementById("blackMinmaxDepth").value;
	}

    shoot() {
        let bestScore;
        let bestMove;

        if(this.white) {
            //maximizing
            bestScore = -Infinity;

            //moves
            let moves = possibleMoves(whitePlayer, true)
            let currentPosition = {row:whitePlayer.row, col:whitePlayer.col};
            for(move of moves) {
                
            }
            //horizontal walls

            //vertical walls
        }
    }
}

function possibleMovesIncludingWalls(white) {
    //{type:0, col:col, row:row}
    let output = [];
    let player;
    if(white) {
        player = whitePlayer;
    } else {
        player = blackPlayer;
    }
        
    //moves
    let type0 = possibleMoves(player, true);
    for(move of type0) {
        output.push({type:0, col:move.col, row:move.row});
    }

    //ver == 1, hor == 2
    if(player.walls > 0) {
        //ver
        for(col in walls.ver) {for(row in walls.ver[col]) {
            if(checkWall(false,col,row)) {
                output.push({type:1, col:col, row:row});
            }
        }}
        //hor
        for(col in walls.hor) {for(row in walls.hor[col]) {
            if(checkWall(true,col,row)) {
                output.push({type:2, col:col, row:row});
            }
        }}
    }

    return output;
    
}

function minimaxSetPlayer(dest, white) {
    if(white) {
        whitePlayer.row = dest.row;
        whitePlayer.col = dest.col;
    } else {
        blackPlayer.row = dest.row;
        blackPlayer.col = dest.col;
    }
}

function minimaxSetWall(hor, dest, add = true) {
    if(add) {
        ////adding a wall////
        if(hor) {
            // console.log(walls.hor);
            walls.hor[dest.col][dest.row] = true;
        } else {
            walls.ver[dest.col][dest.row] = true;
        }
    } else {
        ////removing a wall////
        if(hor) {
            walls.hor[dest.col][dest.row] = false;
        } else {
            walls.ver[dest.col][dest.row] = false;
        }
    }
}

function distance(white) {
    if(white) {
        return shortestPath(whitePlayer).length;
    } else {
        return shortestPath(blackPlayer).length;
    }
}

function checkMovement(white, col, row) {
    let player = white ? whitePlayer : blackPlayer;
    let availableMoves = possibleMoves(player, white);

    return needleInHaystack({col:col, row:row}, availableMoves);
}

function pathfindingPseudoCode() {
    // topleft: gCost == how far it is from starting node
    // topRight: hCost == how far it is from end node
    // bottom: fCost == gCost + hCost

    // 1: check the lowest fCost
    //     from multiple identical fCosts, check the lowest hCost
    //         from multiple identical hCosts, pick one at random
        

    // after everynode check, if it has a checked neighbor, check whether the old sCost or the new is lower and update accordingly (prioritize the lower)

    // open = [] //set of nodes to be evaluated
    // closed = [] //set of ndoes to be evaluated
    // add the starting node to open

    // loop:
    //     current = node in OPEN with lowest fCost
    //     remove current from OPEN
    //     add current to CLOSED

    //     if (current == target node) //path has bee found
    //         return currentNode //then we run a function, running back through all the parent nodes and find the path
        
    //     foreach(neighbour of the current node) {
    //         if nieghbour is wall or neighbor is in CLOSED
    //             skip to next neighbour

    //         if newPath to neighbour is short or neighbor is not in OPEN:
    //             set fCost of neighbour
    //             set parent of neighbor to CURRENT
    //             if niehgbour is not in OPEN:
    //                 add neighbour to OPEN
    //     }
}

function shortestPath(start) {
    let grid = [[],[],[],[],[],[],[],[],[]]; //declaring to make checking O(const);
    let endRow = start.white ? 8: 0;
    // console.log('endRow:', endRow);
    //calculating costs of starting block
    start.g = 0;
    // start.h = (end.row - start.row) + (end.col - start.col);
    start.h = Math.abs(endRow - start.row);
    start.f = start.g + start.h;
    grid[start.col][start.row] = start.g;

    let toCheck = [start];
    let checked = [];
    let current; //just declaration
    let neighbors, neighbor; //also just declaration

    while(toCheck.length > 0) {
        // console.log('------to check not empty------');
        ////finding block with lowest f cost from open////
        let lowInd = 0;
        for(let index = 1; index < toCheck.length; index++) {
          if(toCheck[index].f < toCheck[lowInd].f) { lowInd = index; }
        }
        current = toCheck[lowInd];
        // fillBlock(current.col, current.row, 'magenta');
        // console.log('current:',current);
        // console.log('grid:',grid);
        // console.log('open:',toCheck);
        // console.log('closed:',checked);
        //////////////////////////////////////////////////

        ////if the result has been found////
        if(current.row == endRow) {
            console.log('pathfound');
            // return current;
            let curr = current;
            let path = [];
            while (curr.parent) {
                path.push(curr);
                curr = curr.parent;
            }
            return path.reverse();
        }
        ////////////////////////////////////

        ////normal case: moving current from open to closed, and checking its neighbours////
        toCheck.splice(lowInd, 1);
        checked.push(current);

        neighbors = possibleMoves(current, start.white);
        for(neighbor of neighbors) {
            neighbor.g = current.g + 1;

            //if corresponding node on grid is null, it it's being checked for the first time OR //if the node was checked, compare the new g cost
            if(grid[neighbor.col][neighbor.row] == null || neighbor.g < grid[neighbor.col][neighbor.row]) {
                grid[neighbor.col][neighbor.row] = neighbor.g;
                neighbor.h = Math.abs(endRow - neighbor.row);
                neighbor.f = neighbor.h + neighbor.g;
                neighbor.parent = current;

                //adding to open, if not in open
                if(grid[neighbor.col][neighbor.row] != null) {
                    toCheck.push(neighbor);
                }
                // topLeft(neighbor.col, neighbor.row, neighbor.g);
                // topRight(neighbor.col, neighbor.row, neighbor.h);
                // bottomBottom(neighbor.col, neighbor.row, neighbor.f);
            } 
        }
        ////////////////////////////////////////////////////////////////////////////////////
    }

    //no path was found
    return null;
}

function hasPossiblePath(start) {
    let grid = [[],[],[],[],[],[],[],[],[]]; //declaring to make checking O(const);
    let endRow = start.white ? 8: 0;
    // console.log('endRow:', endRow);
    //calculating costs of starting block
    start.g = 0;
    // start.h = (end.row - start.row) + (end.col - start.col);
    start.h = Math.abs(endRow - start.row);
    start.f = start.g + start.h;
    grid[start.col][start.row] = start.g;

    let toCheck = [start];
    let checked = [];
    let current; //just declaration
    let neighbor; //also just declaration

    while(toCheck.length > 0) {
        // console.log('------to check not empty------');
        ////finding block with lowest f cost from open////
        let lowInd = 0;
        for(let index = 1; index < toCheck.length; index++) {
          if(toCheck[index].f < toCheck[lowInd].f) { lowInd = index; }
        }
        current = toCheck[lowInd];
        // fillBlock(current.col, current.row, 'red');
        // console.log('current:',current);
        // console.log('grid:',grid);
        // console.log('open:',toCheck);
        // console.log('closed:',checked);
        //////////////////////////////////////////////////

        ////if the result has been found////
        if(current.row == endRow) {
            return true;
            // console.log('pathfound');
            // return current;
            // let curr = current;
            // let path = [];
            // while (curr.parent) {
                // path.push(curr);
                // curr = curr.parent;
            // }
            // return path.reverse();
        }
        ////////////////////////////////////

        ////normal case: moving current from open to closed, and checking its neighbours////
        toCheck.splice(lowInd, 1);
        checked.push(current);

        ////top////
        if(checkTop(current)) {
            neighbor = {row: current.row - 1, col: current.col};
            // let gScore = current.g + 1;
            // let gScoreIsBest = false;
            neighbor.g = current.g + 1;
            

            //if corresponding node on grid is null, it it's being checked for the first time OR //if the node was checked, compare the new g cost
            if(grid[neighbor.col][neighbor.row] == null || neighbor.g < grid[neighbor.col][neighbor.row]) {
                grid[neighbor.col][neighbor.row] = neighbor.g;
                neighbor.h = Math.abs(endRow - neighbor.row);
                neighbor.f = neighbor.h + neighbor.g;
                neighbor.parent = current;

                //adding to open, if not in open
                if(grid[neighbor.col][neighbor.row] != null) {
                    toCheck.push(neighbor);
                }
                // topLeft(neighbor.col, neighbor.row, neighbor.g);
                // topRight(neighbor.col, neighbor.row, neighbor.h);
                // bottomBottom(neighbor.col, neighbor.row, neighbor.f);
            } 
        }

        ////down////
        if(checkDown(current)) {
            neighbor = {row: current.row + 1, col: current.col};
            // let gScore = current.g + 1;
            // let gScoreIsBest = false;
            neighbor.g = current.g + 1;
            

            //if corresponding node on grid is null, it it's being checked for the first time OR //if the node was checked, compare the new g cost
            if(grid[neighbor.col][neighbor.row] == null || neighbor.g < grid[neighbor.col][neighbor.row]) {
                grid[neighbor.col][neighbor.row] = neighbor.g;
                neighbor.h = Math.abs(endRow - neighbor.row);
                neighbor.f = neighbor.h + neighbor.g;
                neighbor.parent = current;

                //adding to open, if not in open
                if(grid[neighbor.col][neighbor.row] != null) {
                    toCheck.push(neighbor);
                }
                // topLeft(neighbor.col, neighbor.row, neighbor.g);
                // topRight(neighbor.col, neighbor.row, neighbor.h);
                // bottomBottom(neighbor.col, neighbor.row, neighbor.f);
            } 
        }

        ////left////
        if(checkLeft(current)) {
            neighbor = {row: current.row, col: current.col - 1};
            // let gScore = current.g + 1;
            // let gScoreIsBest = false;
            neighbor.g = current.g + 1;
            

            //if corresponding node on grid is null, it it's being checked for the first time OR //if the node was checked, compare the new g cost
            if(grid[neighbor.col][neighbor.row] == null || neighbor.g < grid[neighbor.col][neighbor.row]) {
                grid[neighbor.col][neighbor.row] = neighbor.g;
                neighbor.h = Math.abs(endRow - neighbor.row);
                neighbor.f = neighbor.h + neighbor.g;
                neighbor.parent = current;

                //adding to open, if not in open
                if(grid[neighbor.col][neighbor.row] != null) {
                    toCheck.push(neighbor);
                }
                // topLeft(neighbor.col, neighbor.row, neighbor.g);
                // topRight(neighbor.col, neighbor.row, neighbor.h);
                // bottomBottom(neighbor.col, neighbor.row, neighbor.f);
            } 
        }

        ////right////
        if(checkRight(current)) {
            neighbor = {row: current.row, col: current.col + 1};
            // let gScore = current.g + 1;
            // let gScoreIsBest = false;
            neighbor.g = current.g + 1;
            

            //if corresponding node on grid is null, it it's being checked for the first time OR //if the node was checked, compare the new g cost
            if(grid[neighbor.col][neighbor.row] == null || neighbor.g < grid[neighbor.col][neighbor.row]) {
                grid[neighbor.col][neighbor.row] = neighbor.g;
                neighbor.h = Math.abs(endRow - neighbor.row);
                neighbor.f = neighbor.h + neighbor.g;
                neighbor.parent = current;

                //adding to open, if not in open
                if(grid[neighbor.col][neighbor.row] != null) {
                    toCheck.push(neighbor);
                }
                // topLeft(neighbor.col, neighbor.row, neighbor.g);
                // topRight(neighbor.col, neighbor.row, neighbor.h);
                // bottomBottom(neighbor.col, neighbor.row, neighbor.f);
            } 
        }
        ////////////////////////////////////////////////////////////////////////////////////
    }

    //no path was found
    return false;
}

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



