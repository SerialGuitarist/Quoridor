import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import os
import random
from collections import deque
import torch.nn.functional as F
import time

from gameState import GameState
from agent import Agent

MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

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
        self.conv1 = nn.Conv2d(4, 32, 3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.conv3 = nn.Conv2d(64, 64, 3, padding=1)

        ## fully connected feed forward layers
        ## 64 for the convd
        ## 2 for len of shortest white path, and shortest black path
        ## 2 for white and black walls
        ## 1 for turn (0 or 1) (now normalized to always be white)
        self.fc1 = nn.Linear(64*9*9 + 5, 256)
        self.fc2 = nn.Linear(256, 64)
        self.out = nn.Linear(64, 1)


    def forward(self, board, features):
        ## convo layers
        x = F.leaky_relu(self.conv1(board), negative_slope=0.1)
        x = F.leaky_relu(self.conv2(x), negative_slope=0.1)
        x = F.leaky_relu(self.conv3(x), negative_slope=0.1)

        ## gonna try without global average pooling
        ## preserve spatial structure
        x = torch.flatten(x, start_dim=1)  ## (B, 64*9*9)

        ## concatenate handcrafted features like shortest paths lengths
        x = torch.cat([x, features], dim=1)

        ## value head linear layers
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.out(x)

        return x


class ScoringAgent(Agent):
    def __init__(self, 
                 path="version_4.pth",  ## where the model is saved
                 losses_path="losses.txt", ## where to log losses to
                 lr=1e-3,  
                 batch_size=2**8,  
                 gamma=0.99, ## discount factor for qlearning
                 memory_size=100_000, ## how many latest game states to remember
                 delay=0, ## how many seconds to wait before making a move
                 tau_move=0.2, ## how much to flatten the distribution of scores
                 tau_wall=1.5):
        self.model = ScoringModel().to(device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.criterion = nn.MSELoss()

        ## target net
        ## tldr: use this to make predictions, while training the actual model
        ## and only update the actualy model every 100 or so epochs for added
        ## stability
        self.target = ScoringModel().to(device)
        self.target.load_state_dict(self.model.state_dict())

        self.memory = deque(maxlen=memory_size) ## replay buffer
        self.batch_size = batch_size
        self.gamma = gamma ## discount factor for qlearning
        self.path = os.path.join(MODELS_DIR, path)
        self.delay = delay
        self.losses_path = losses_path
        self.tau_move = 0.2 ## sharp = greedy
        self.tau_wall = 1.5 ## wider = exploratory
        self.training_steps = 0
        self.load()


    ## teh "canon form" is one where white is about to move
    ## creates a copy and doesnt change original
    ## DEPRECATED, no longer used
    def canonicalize(self, state: GameState):
        if state.turn == 0:
            s = state.copy()
            s.flip()
            return s
        return state

    def preprocess_state(self, state):
        ## walls is (2,8,8) vector where first 8x8 is vertical walls and second 8x8 is horizontal walls
        ## agents is (2, 3) vector
        ## agents[0] is black
        ## angets[1] is white
        ## agents[1][0] is white y coord (row)
        ## agents[1][1] is white x coord (col)
        ## agents[1][2] is walls white has left
        ## and vice versa
        ## state.turn is 1 for white and 0 for black

        board = np.zeros((4, 9, 9), dtype=np.float32)

        ## walls padded to 9x9
        board[0, :8, :8] = state.walls[0] ## vertical
        board[1, :8, :8] = state.walls[1] ## horizontal

        ## agent positions
        board[2, state.agents[0][0], state.agents[0][1]] = 1    ## black
        board[3, state.agents[1][0], state.agents[1][1]] = 1    ## white

        features = np.array([
            float(len(state.shortestPath(1))) / 16, ## white distance
            float(len(state.shortestPath(0))) / 16, ## black distance
            float(state.agents[1][2]) / 10, ## white walls left
            float(state.agents[0][2]) / 10, ## black walls left
            float(state.turn)
        ], dtype=np.float32)

        ## converting to pytorch tensors
        ## unsqueeze adds adds a batch dimension at the start
        ## to(device) moves it over to gpu for faster because pytorch does
        ##  not automatically move the data and throws errors
        board_tensor = torch.tensor(board).unsqueeze(0).to(device)  ## (1, 5, 9, 9)
        features_tensor = torch.tensor(features).unsqueeze(0).to(device)    ## (1, 4)

        return board_tensor, features_tensor

    def score(self, state):
        ## set model to eval mode
        self.model.eval()

        ## dont calculate gradient when just scoring
        with torch.no_grad():
            board, features = self.preprocess_state(state)
            return self.model(board, features).item()

    def batch_score(self, states, use_target=False):
        ## set model to eval mode
        network = self.target if use_target else self.model
        network.eval()

        ## dont calculate gradient when just scoring
        with torch.no_grad():
            batch_boards, batch_features = zip(*[self.preprocess_state(s) for s in states])
            batch_boards = torch.cat(batch_boards, dim=0)   ## (batch_size, 4, 9, 9)
            batch_features = torch.cat(batch_features, dim=0)     ## (batch_size, 4)
            scores = network(batch_boards, batch_features)
        return scores.squeeze(-1) ## returning a tensor instea of a list

    # ## computes max_a (-V(s')) for a canonicalized state.
    # def best_next_value(self, state: GameState):
        # next_states = state.moveStates() + state.wallStates()
        # if not next_states:
            # return 0.0
# 
        # views = [self.canonicalize(s) for s in next_states]
# 
        # # with torch.no_grad():
            # # v_next = self.batch_score(views)  ## shape (N,)
            # # best = torch.max(v_next).item() ## best move for opponent
# 
        # with torch.no_grad():
            # batch_boards, batch_features = zip(*[self.preprocess_state(s) for s in views])
            # batch_boards = torch.cat(batch_boards, dim=0)
            # batch_features = torch.cat(batch_features, dim=0)
            # v_next = self.target(batch_boards, batch_features).squeeze(-1)  # ← Use target!
            # best = torch.max(v_next).item()
# 
        # return -best ## negatve because it's opponent's turn


    ## tau controlled softmax
    def shoot(self, state): #, epsilon=0.1):
        time.sleep(self.delay)

        ## split actions
        move_states = state.moveStates()
        wall_states = state.wallStates()

        # ## epsilon greedy exploration
        # if random.random() < epsilon:
            # return random.choice(move_states + wall_states)

        ## score scuccessors (taking into account sometimes you cant move/wall)
        move_scores = self.batch_score(move_states) if move_states else None
        wall_scores = self.batch_score(wall_states) if wall_states else None

        ## if it's black's turn (turn=0), black wants low score
        ## if it's white's turn (turn=1), white wants high score
        if state.turn == 0:
            move_scores = -move_scores
            if wall_scores is not None:  # ← Add this check
                wall_scores = -wall_scores
        
        ## mixture weights
        ## makes moves more preferable over walls so the wall states
        ## dont drown out the move states by sheer numbers
        p_move = 0.9
        # p_wall = 1 - p_move ## technically not necessary
        ## sample which group first
        if random.random() < p_move or len(wall_states) == 0: ## move states is never empty
            probs = F.softmax(move_scores / self.tau_move, dim=0)
            idx = torch.multinomial(probs , 1).item()
            return move_states[idx]
        else:
            probs = F.softmax(wall_scores / self.tau_wall, dim=0)
            idx = torch.multinomial(probs , 1).item()
            return wall_states[idx]

# 
        # ## sample which group first
        # if random.random() < p_move:
            # idx = torch.multinomial(move_probs, 1).item()
            # return move_states[idx]
        # else:
            # idx = torch.multinomial(wall_probs, 1).item()
            # return wall_states[idx]


        # ## approximate the q score by comparing v_next and v_now
        # # qscores = v_next - v_state
        # # ## clamping for numeric stability
        # # qscores = torch.clamp(qscores, -5.0, 5.0)
        # if move_v is not None:
            # # move_q = torch.clamp(move_v - v_state, -5.0, 5.0)
            # move_q = torch.clamp(move_v, -5.0, 5.0)
        # if wall_v is not None:
            # # wall_q = torch.clamp(wall_v - v_state, -5.0, 5.0)
            # wall_q = torch.clamp(wall_v, -5.0, 5.0)
# 
        # ## degenerate cases
        # if not wall_states:
            # probs = F.softmax(move_q / self.tau_move, dim=0)
            # return move_states[torch.multinomial(probs, 1).item()]
# 
        # if not move_states:
            # probs = F.softmax(wall_q / self.tau_wall, dim=0)
            # return wall_states[torch.multinomial(probs, 1).item()]
# 
        # ## group softmaxes
        # move_probs = F.softmax(move_q / self.tau_move, dim=0)
        # wall_probs = F.softmax(wall_q / self.tau_wall, dim=0)
# 
        # ## mixture weights
        # ## if calculations are right, makes move states ~400 times
        # ## more preferable, which should cancel out there being ~100 times
        # ## more wall states than move states most of the time
        # p_move = 0.9
        # p_wall = 0.1
# 
        # ## sample which group first
        # if random.random() < p_move:
            # idx = torch.multinomial(move_probs, 1).item()
            # return move_states[idx]
        # else:
            # idx = torch.multinomial(wall_probs, 1).item()
            # return wall_states[idx]


    ## epsilon greedy exploration
    # def shoot(self, state, epsilon=0.1):
    # states = state.possibleGameStates()
    # scores = self.batch_score(states)
    # # print(scores)
    # if np.random.rand() < epsilon:
    # return random.choice(states)
    # else:
    # return states[np.argmax(scores) if state.turn else np.argmin(scores)]


    ## training logic stuff
    ## storing experiences for training
    def remember(self, state, next_state, reward):
        self.memory.append((state, next_state, reward))
        # s = self.canonicalize(state)
        # ns = self.canonicalize(next_state) if next_state else None
        # self.memory.append((s, ns, reward))

    def replay(self):
        if len(self.memory) < self.batch_size:
            return 0.0

        batch = random.sample(self.memory, self.batch_size)
        batch_boards = []
        batch_features = []
        batch_targets = []

        for state, next_state, reward in batch:
            board, features = self.preprocess_state(state)
            target_v = reward

            ## add discounted future value
            if next_state is not None:
                next_states = next_state.possibleGameStates()
                if next_states:
                    next_scores = self.batch_score(next_states, use_target=True)

                    ## opponent picks their best move under minimax
                    if next_state.turn == 0:  ## black's turn next
                        best_next = torch.min(next_scores).item()
                    else:  ## white's turn next
                        best_next = torch.max(next_scores).item()
                    target_v += self.gamma * best_next


            # target_v = reward
#
            # if next_state is not None:
                # with torch.no_grad():
                    # # next_board, next_features = self.preprocess_state(ns_view)
                    # next_board, next_features = self.preprocess_state(next_state)
                    # ## with canonicalization, next board is the enemy's score
                    # ## so we gotta subtract it instead of adding
                    # target_v += self.gamma * (-self.target(next_board, next_features).item())

            batch_boards.append(board)
            batch_features.append(features)
            batch_targets.append(target_v)

        ## converting to tensors
        batch_boards = torch.cat(batch_boards, dim=0)
        batch_features = torch.cat(batch_features, dim=0)
        batch_targets = torch.tensor(batch_targets, dtype=torch.float32, device=device).unsqueeze(1)

        ## training step
        self.model.train()
        ## clears accumulated gradients from previous training step
        self.optimizer.zero_grad()
        ## forward pass over the batch of games
        predictions = self.model(batch_boards, batch_features)
        ## calculating loss
        loss = self.criterion(predictions, batch_targets)
        loss.backward()
        ## gradient clip for stabilitiy
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        ## apply the calculated delta weights
        self.optimizer.step()
        self.training_steps += 1

        return loss.item()

    ## play a single game and return history
    def play_one_game(self, max_steps=256):
        state = GameState.newGame()
        history = []

        for step in range(max_steps):
            next_state = self.shoot(state) #, epsilon)

            winner = next_state.checkVictory()
            if winner >= 0:
                if winner == 1: ## white won
                    reward = 1.0
                else:           ## black won
                    reward = -1.0

                history.append((state, next_state, reward))
                history.append((next_state, None, reward))
                return history, False
            else:
                reward = 0.0
                history.append((state, next_state, reward))
                state = next_state

        return history, True

    def train(self, num_epochs=10000, save_every=50, games_per_epoch=5):
        print("Starting Training")
        self.model.train()

        # ## epsilon greedy that decays over time
        # epsilon = 0.5
        # epsilon_decay = 0.997
        # epsilon_min = 0.05

        for epoch in range(1, num_epochs+1):
            print(log := f"Step:{self.training_steps}; Hist: [", end="")
            game_logs = []

            for _ in range(games_per_epoch):
                history, broken = self.play_one_game()

                if not broken:
                    ## final winner: terminal player has lost
                    temp = str(len(history))
                    game_logs.append(temp)
                    print(temp + ",", end="")

                    for state, next_state, reward in history:
                        self.remember(state, next_state, reward)

                        ## data augmentation
                        ## mirror augmentation
                        s_mirror = state.copy()
                        s_mirror.mirror()
                        ns_mirror = next_state.copy() if next_state else None
                        if ns_mirror:
                            ns_mirror.mirror()
                        self.remember(s_mirror, ns_mirror, reward)
                        ## flipping augmentation also possible
                else:
                    temp = "(b)"
                    game_logs.append(temp)
                    print(temp + ",", end="")


            ## training multiple times per epoch
            losses = []
            for _ in range(games_per_epoch * 2):
                loss = self.replay()
                losses.append(loss)
            losses_view = "[" + ",".join(map(lambda l : f"{l:.4f}", losses)) + "]"
            temp = f"]; Mem:{len(self.memory)}; Losses:{losses_view}; "
            print(temp, end="\n")
            log += temp

            ## decay exploration
            # epsilon = max(epsilon_min, epsilon * epsilon_decay)

            ## update target network periodically
            if epoch % 50 == 0:
                self.target.load_state_dict(self.model.state_dict())

            with open(self.losses_path, "a") as f:
                f.write(f"{log}\n")

            ## save our progress
            if epoch % save_every == 0:
                self.save()

    def save(self, path=None, epoch=None):
        if path is None:
            if epoch is not None:
                path = os.path.join(MODELS_DIR, f"model_epoch_{epoch}.pth")
            else:
                # path = os.path.join(MODELS_DIR, "latest.pth")
                path = self.path

        torch.save({
            "model_state_dict": self.model.state_dict(),
            "target_state_dict": self.target.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "training_steps": self.training_steps,
        }, path)

        print("Model saved to", path)

    def load(self, path=None):
        if path is None:
            path = self.path

        if os.path.exists(path):
            print("Loading saved model from", path)
            checkpoint = torch.load(path, map_location=device)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.target.load_state_dict(checkpoint["target_state_dict"])
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            self.training_steps = checkpoint.get("training_steps", 0)
            print("Model loaded")
        else:
            print("No saved model found at", path)


if __name__ == "__main__":
    agent = ScoringAgent()
    agent.train(num_epochs=1_000_000, save_every=50)

