import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import os
import random
from collections import deque
import torch.nn.functional as F
import time

import json

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
        ## DEPRECATED: 1 for turn (0 or 1) (now normalized to always be white)
        self.fc1 = nn.Linear(64*9*9 + 4, 256)
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
    def __init__(self, path="version_3.pth", losses_path="losses.txt", lr=1e-3, batch_size=2**8, gamma=0.99, memory_size=100_000, delay=0, tau=1.5, tau_move=0.2, tau_wall=1.5):
        self.model = ScoringModel().to(device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.criterion = nn.MSELoss()
        self.memory = deque(maxlen=memory_size) ## replay buffer
        self.batch_size = batch_size
        self.gamma = gamma ## discount factor for qlearning
        self.path = path
        self.delay = delay
        self.tau = tau
        self.losses_path = losses_path
        self.tau_move = 0.2 ## sharp = greedy
        self.tau_wall = 1.5 ## wider = exploratory
        self.load()

        ## something something target net
        self.target = ScoringModel().to(device)
        self.target.load_state_dict(self.model.state_dict())

    ## teh "canon form" is one where white is about to move
    ## creates a copy and doesnt change original
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

        # canonicalize so mover is white
        # just realized this is getting canonicalized earlier in remember anyway
        # state = self.canonicalize(state)

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
            float(state.agents[1][2]) / 10,
            float(state.agents[0][2]) / 10,
            # float(state.turn)
        ], dtype=np.float32)

        ## converting to pytorch tensors
        ## unsqueeze adds adds a batch dimension at the start
        ## to(device) moves it over to gpu for faster because pytorch does
        ##  not automatically move the data and throws errors
        board_tensor = torch.tensor(board).unsqueeze(0).to(device)  ## (1, 4, 9, 9)
        features_tensor = torch.tensor(features).unsqueeze(0).to(device)    ## (1, 4)

        return board_tensor, features_tensor

    def score(self, state):
        ## set model to eval mode
        self.model.eval()

        ## dont calculate gradient when just scoring
        with torch.no_grad():
            board, features = self.preprocess_state(state)
            return self.model(board, features).item()

    def batch_score(self, states):
        ## set model to eval mode
        self.model.eval()

        ## dont calculate gradient when just scoring
        with torch.no_grad():
            batch_boards, batch_features = zip(*[self.preprocess_state(s) for s in states])
            batch_boards = torch.cat(batch_boards, dim=0)   ## (batch_size, 4, 9, 9)
            batch_features = torch.cat(batch_features, dim=0)     ## (batch_size, 4)
            scores = self.model(batch_boards, batch_features)
        return scores.squeeze(-1) ## returning a tensor instea of a list

    def best_next_value(self, state: GameState):
        """
        Computes max_a (-V(s')) for a canonicalized state.
        """
        next_states = state.moveStates() + state.wallStates()
        if not next_states:
            return 0.0

        views = [self.canonicalize(s) for s in next_states]

        with torch.no_grad():
            v_next = self.batch_score(views)  # shape (N,)
            best = torch.max(-v_next).item()

        return best


    ## tau controlled softmax
    def shoot(self, state):
        time.sleep(self.delay)

        ## split actions
        move_states = state.moveStates()
        wall_states = state.wallStates()

        ## canonize current state
        state_view = self.canonicalize(state)
        # v_state = torch.tensor(self.score(state_view), device=device)

        ## canonize successors
        move_views = [self.canonicalize(s) for s in move_states]
        wall_views = [self.canonicalize(s) for s in wall_states]

        ## score scuccessors (taking into account sometimes you cant move/wall)
        move_v = self.batch_score(move_views) if move_views else None
        wall_v = self.batch_score(wall_views) if wall_views else None

        ## approximate the q score by comparing v_next and v_now
        # qscores = v_next - v_state
        # ## clamping for numeric stability
        # qscores = torch.clamp(qscores, -5.0, 5.0)
        if move_v is not None:
            # move_q = torch.clamp(move_v - v_state, -5.0, 5.0)
            move_q = torch.clamp(-move_v, -5.0, 5.0)
        if wall_v is not None:
            # wall_q = torch.clamp(wall_v - v_state, -5.0, 5.0)
            wall_q = torch.clamp(-wall_v, -5.0, 5.0)

        ## degenerate cases
        if not wall_states:
            probs = F.softmax(move_q / self.tau_move, dim=0)
            return move_states[torch.multinomial(probs, 1).item()]

        if not move_states:
            probs = F.softmax(wall_q / self.tau_wall, dim=0)
            return wall_states[torch.multinomial(probs, 1).item()]

        ## group softmaxes
        move_probs = F.softmax(move_q / self.tau_move, dim=0)
        wall_probs = F.softmax(wall_q / self.tau_wall, dim=0)

        ## mixture weights
        ## if calculations are right, makes move states ~400 times
        ## more preferable, which should cancel out there being ~100 times
        ## more wall states than move states most of the time
        p_move = 0.9
        p_wall = 0.1

        ## sample which group first
        if random.random() < p_move:
            idx = torch.multinomial(move_probs, 1).item()
            return move_states[idx]
        else:
            idx = torch.multinomial(wall_probs, 1).item()
            return wall_states[idx]


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
        s = self.canonicalize(state)
        ns = self.canonicalize(next_state) if next_state else None
        self.memory.append((s, ns, reward))

    def replay(self):
        if len(self.memory) < self.batch_size:
            return 0.0

        batch = random.sample(self.memory, self.batch_size)
        batch_boards = []
        batch_features = []
        batch_qscores = []

        for state, next_state, reward in batch:
            board, features = self.preprocess_state(state)
            target_v = reward

            if next_state is not None:
                best_next = self.best_next_value(next_state)
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
            batch_qscores.append(target_v)


        batch_boards = torch.cat(batch_boards, dim=0)
        batch_features = torch.cat(batch_features, dim=0)
        batch_qscores = torch.tensor(batch_qscores, dtype=torch.float32, device=device).unsqueeze(1)

        ## clears accumulated gradients from previous training step
        self.optimizer.zero_grad()
        ## forward pass over the batch of games
        predictions = self.model(batch_boards, batch_features)
        ## calculating loss
        loss = self.criterion(predictions, batch_qscores)
        # for name, param in self.model.named_parameters():
        # if param.grad is not None:
        # print(f"{name} gradient mean: {param.grad.mean().item()}")
        ## backpropagation
        # print(f"Loss before backward: {loss.item()}")
        loss.backward()
        # print(f"Loss after backward: {loss.item()}")
        ## gradient clip for stabilitiy
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        ## apply the calculated delta weights
        self.optimizer.step()
        ## soemthing soemthing target net
        with torch.no_grad():
            for p, tp in zip(self.model.parameters(), self.target.parameters()):
                tp.data.lerp_(p.data, 0.005)



        return loss.item()

    def train(self, num_epochs=1000, save_every=50):
        print("Starting Training")
        self.model.train()
        loss_history = []

        ## dynamically increases tau later
        ## higher tau = flatter distro, more exploration
        ## lower tau = sharper distro, more exploitation
        ## intuition is as the training progresses, you wanna exploit more
        # saved_tau = self.tau
        ## quick and dirty tau stuff
        # tau_start = 2.0
        # tau_end = 0.5
        for epoch in range(1, num_epochs+1):
            print(f"Epoch:{epoch}; Hist:", end="")
            state = GameState.newGame()
            history = []
            # self.tau = min(2.0, 0.5 + epoch / 200_000)  ## gradually increase exploration
            # self.tau = tau_end + (tau_start - tau_end) * max(0, 1 - epoch / num_epochs)

            ## used to discard any game that takes more than 256 steps
            broken = False

            prev_state = None

            while state.checkVictory() < 0:
                ## shoot() minimizes opponent's score
                next_state = self.shoot(state)
                ## canonical views for shaping (mover-is-white both times)
                s_view  = self.canonicalize(state)
                ns_view = self.canonicalize(next_state)

                cur_w = len(s_view.shortestPath(1)); cur_b = len(s_view.shortestPath(0))
                nxt_w = len(ns_view.shortestPath(1)); nxt_b = len(ns_view.shortestPath(0))

                ## potential-based shaping (safe): Φ(s) = -(dW - dB)/16
                phi_cur = - (cur_w - cur_b) / 16.0
                phi_nxt = - (nxt_w - nxt_b) / 16.0

                reward  = 0.5 * (self.gamma * phi_nxt - phi_cur) ## fine tune the 0.5 weight later

                ## reward decreasing own path
                # reward += 0.05 * max(0, cur_w - nxt_w)

                ## reward wall placement that increases opponent path
                # reward += 0.05 * max(0, nxt_b - cur_b)


                ## small step cost and wall-use cost (no turn sign needed anymore)
                if ns_view.agents[1][2] < s_view.agents[1][2]:
                    reward -= 0.005
                reward -= 0.01

                ## big reward for terminal states
                winner = next_state.checkVictory()
                if winner >= 0:
                    ## if the player who just moved won
                    if winner == state.turn:
                        reward += 2.0
                    else:
                        reward -= 2.0

                ## small punishment for going back to the same state
                if prev_state is not None and next_state == prev_state:
                    reward -= 0.05
                prev_state = state

                history.append((state, next_state, reward))
                state = next_state
                if len(history) > 256:
                    print("broken; ", end="")
                    broken = True
                    break

            if not broken:
                ## final winner: terminal player has lost
                history.append((state, None, -1.0))
                print(f"{len(history)}; ", end="")
                # winner = state.checkVictory() ## 0 for black, 1 for white
                # reward = 1.0 if winner == 1 else -1.0
                # for i, (s, ns, r_, d) in enumerate(history):
                # history[i] = (s, ns, reward)
                # history.append((state, None, reward))
                # print(f"{len(history)}; ", end="")

                for state, next_state, reward in history:
                    self.remember(state, next_state, reward)
                    ## data augmentation
                    ## mirror augmentation
                    s_ = state.copy()
                    s_.mirror()
                    ns_ = None
                    if next_state:
                        ns_ = next_state.copy()
                        ns_.mirror()
                    self.remember(s_, ns_, reward)

                    ## flipping augmentation
                    s_f = state.copy()
                    s_f.flip()
                    ns_f = None
                    if next_state:
                        ns_f = next_state.copy()
                        ns_f.flip()
                    self.remember(s_f, ns_f, reward)


                # for experience in history:
                # self.remember(*experience)

                if not state.hasValidPath(0) or not state.hasValidPath(1):
                    printBoard(state)
                    print(state.toSerial())


            loss = self.replay()
            loss_history.append(loss)
            print(f"Mem:{len(self.memory)}; Loss:{loss:.4f}")
            # if loss > 1000:
            # printBoard(state)

            if epoch % save_every == 0:
                self.save()
                with open(self.losses_path, "a") as f:
                    f.write(f"{loss_history}\n")

    def save(self, path=None, epoch=None):
        if path is None:
            if epoch is not None:
                path = os.path.join(MODELS_DIR, f"model_epoch_{epoch}.pth")
            else:
                path = os.path.join(MODELS_DIR, "latest.pth")

        torch.save({
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict()
        }, path)

        print("Model saved to", path)

    def load(self, path=None):
        if path is None:
            path = os.path.join(MODELS_DIR, "latest.pth")

        if os.path.exists(path):
            print("Loading saved model from", path)
            checkpoint = torch.load(path, map_location=device)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            print("Model loaded")
        else:
            print("No saved model found at", path)


if __name__ == "__main__":
    agent = ScoringAgent()
    agent.train(num_epochs=1_000_000, save_every=50)

