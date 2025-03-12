import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import os
import random
from collections import deque


from gameState import GameState
from agent import Agent

## Get cpu, gpu or mps device for training.
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using {device} device")


class ScoringModel(nn.Module):
    def __init__(self):
        super().__init__()
        
        ## convo layers
        ## in channels:
        ## - 1 hot black location
        ## - 1 hot white location
        ## - black walls
        ## - white walls
        self.conv1 = nn.Conv2d(
                in_channels = 4,
                out_channels = 32,
                kernel_size = 3,
                padding = 1
        )

        self.conv2 = nn.Conv2d(
                in_channels = 32,
                out_channels = 64,
                kernel_size = 3,
                padding = 1
        )

        ## no pooling layers
        
        ## fully connected feed forward layers
        ## 3 for walls each side has remaining and whose turn it is
        self.linear1 = nn.Linear(64 * 9 * 9 + 3, 256) 
        self.linear2 = nn.Linear(256, 64)
        self.output = nn.Linear(64, 1)


    def forward(self, board, walls_n_turn):
        ## convo layers
        x = torch.relu(self.conv1(board))
        x = torch.relu(self.conv2(x))

        ## flatten walls
        x = torch.flatten(x, start_dim=1)

        ## merging board with walls and turn
        x = torch.cat((x, walls_n_turn), dim=1)

        ## linear layers
        x = torch.relu(self.linear1(x))
        x = torch.relu(self.linear2(x))
        x = self.output(x)
        return x


class ScoringAgent(Agent):
    def __init__(self, path="scoring.pth", lr=0.001, batch_size=32, gamma=0.99, memory_size=10000, delay=0):
        self.model = ScoringModel().to(device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.criterion = nn.MSELoss()
        self.memory = deque(maxlen=memory_size) ## replay buffer
        self.batch_size = batch_size
        self.gamma = gamma ## discount factor for qlearning
        self.path = path
        self.delay = delay

        self.load()

        self.delay = delay
    
    def preprocess_state(self, state):
        ## walls is (2,8,8) vector where first 8x8 is vertical walls and second 8x8 is horizontal walls
        ## agents is (2, 3) vector
            ## agents[0] is black
            ## angets[1] is white
            ## agents[1][0] is white y coord (row)
            ## agents[1][1] is white x coord (col)
            ## agents[1][2] is walls white has left
            ## and vice versa
        board = np.zeros((4, 9, 9), dtype=np.float32)

        ## walls padded to 9x9
        board[0, :8, :8] = state.walls[0] ## vertical
        board[1, :8, :8] = state.walls[1] ## horizontal

        ## agent positions
        board[2, state.agents[0][0], state.agents[0][1]] = 1    ## black
        board[3, state.agents[1][0], state.agents[1][1]] = 1    ## white

        walls_n_turn = np.array([
            state.agents[0][2],
            state.agents[1][2],
            state.turn
        ])

        ## converting to pytorch tensors
        ## unsqueeze adds adds a batch dimension at the start
        ## to(device) moves it over to gpu for faster because pytorch does
        ##  not automatically move the data and throws errors
        board_tensor = torch.tensor(board).unsqueeze(0).to(device)  ## (1, 4, 9, 9)
        walls_tensor = torch.tensor(walls_n_turn).unsqueeze(0).to(device)    ## (1, 3)

        return board_tensor, walls_tensor

    def score(self, state):
        ## set model to eval mode
        self.model.eval() 

        ## dont calculate gradient when just scoring
        with torch.no_grad():
            board, walls_n_turn = self.preprocess_state(state)
            return self.model(board, walls_n_turn).item()

    def batch_score(self, states):
        ## set model to eval mode
        self.model.eval() 

        ## dont calculate gradient when just scoring
        with torch.no_grad():
            batch_boards = []
            batch_walls = []

            for state in states:
                board, walls_n_turn = self.preprocess_state(state)
                batch_boards.append(board)
                batch_walls.append(walls_n_turn)
            
            ## tensors into batches
            batch_boards = torch.cat(batch_boards, dim=0)  ## (batch_size, 4, 9, 9)
            batch_walls = torch.cat(batch_walls, dim=0)    ## (batch_size, 3)

            scores = self.model(batch_boards, batch_walls)

        return scores.squeeze(-1).tolist()
        
    ## epsilon greedy exploration
    def shoot(self, state, epsilon=0.1):
        states = state.possibleGameStates()
        scores = self.batch_score(states)
        # print(scores)
        if np.random.rand() < epsilon:
            return random.choice(states)
        else:
            return states[np.argmax(scores) if state.turn else np.argmin(scores)]


    ## training logic stuff
    ## storing experiences for training
    def remember(self, state, next_state, reward, done):
        self.memory.append((state, next_state, reward, done))

    def replay(self):
        if len(self.memory) < self.batch_size:
            return 0.0

        batch = random.sample(self.memory, self.batch_size)
        batch_boards = []
        batch_walls_n_turns = []
        batch_qscores = []

        for state, next_state, reward, done in batch:
            board, walls_n_turns = self.preprocess_state(state)
            qscore = reward ## i am 90% this is the qscore and not the vscore

            if not done:
                with torch.no_grad():
                    next_board, next_walls_n_turn = self.preprocess_state(next_state)
                    qscore += self.gamma * self.model(next_board, next_walls_n_turn).max().item()

            batch_boards.append(board)
            batch_walls_n_turns.append(walls_n_turns)
            batch_qscores.append(qscore)


        batch_boards = torch.cat(batch_boards, dim=0)
        batch_walls_n_turns = torch.cat(batch_walls_n_turns, dim=0)
        batch_qscores = torch.tensor(batch_qscores, dtype=torch.float32, device=device).unsqueeze(1)

        ## clears accumulated gradients from previous training step
        self.optimizer.zero_grad()
        ## forward pass over the batch of games
        predictions = self.model(batch_boards, batch_walls_n_turns)
        ## calculating loss
        loss = self.criterion(predictions, batch_qscores)
        # for name, param in self.model.named_parameters():
            # if param.grad is not None:
                # print(f"{name} gradient mean: {param.grad.mean().item()}")
        ## backpropagation
        # print(f"Loss before backward: {loss.item()}")
        loss.backward()
        # print(f"Loss after backward: {loss.item()}")
        ## apply the calculated delta weights
        self.optimizer.step()

        return loss.item()

    def train(self, num_epochs=1000, save_every=50):
        print("Starting Training")
        for epoch in range(1, num_epochs+1):
            print(f"Starting {epoch}/{num_epochs}")
            state = GameState.newGame()
            history = []

            while state.checkVictory() < 0:
                next_state = self.shoot(state)

                ## reward shenanigans
                shortest_path = len(state.shortestPath(state.turn))
                delta_dist = len(next_state.shortestPath(state.turn)) - shortest_path
                delta_other_dist = len(next_state.shortestPath(1-state.turn)) - len(state.shortestPath(1-state.turn))
                reward = 0
                reward -= delta_dist * .1 ## rewarding progress
                reward += delta_other_dist * .1 ## rewarding good wall placement
                reward -= 0.01 ## punishing not having won yet

                done = False

                history.append((state, next_state, reward, done))
                state = next_state

            ## final winner
            winner = state.checkVictory() ## 0 for black, 1 for white
            reward = 1 if winner == 1 else -1
            # for i, (s, ns, r_, d) in enumerate(history):
                # history[i] = (s, ns, reward, done)
            history.append((state, None, reward, True))

            for experience in history:
                self.remember(*experience)

            loss = self.replay()
            print(f"Epoch {epoch}, Loss: {loss:.4f}")

            if epoch % save_every == 0:
                self.save()

    def save(self, path=None):
        if path==None:
            path = self.path
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict()
        }, self.path)
        print("Model saved to", path)

    def load(self, path=None):
        if path==None:
            path = self.path
        if os.path.exists(self.path):
            print("Loading saved model from", {path})
            checkpoint = torch.load(self.path, map_location=device)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            print("Model loaded")
        else:
            print("No saved model found at", path)

if __name__ == "__main__":
    agent = ScoringAgent()
    agent.train(num_epochs=1000, save_every=25)
