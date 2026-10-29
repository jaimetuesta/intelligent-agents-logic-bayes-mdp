# Intelligent Agents in an *Apocalypse Now*-Inspired Scenario: Logic, Bayesian Inference and MDPs

**Author:** Jaime Tuesta de Simón (individual project)
**Context:** Final project of *Fundamentos de Inteligencia Artificial* (Foundations of AI), 2nd year, Universidad Pontificia Comillas (ICAI), January 2026.
**Language:** code comments, console messages and report are in Spanish; this README is in English.

## Overview

Captain Willard must find Colonel Kurtz in a hidden 6×6 palace and escape with him, and later cross a river with currents. The project solves these scenarios with three classic AI techniques, each in its own console program:

| Program | Technique | What it does |
|---|---|---|
| `kurtz.py` | Logical agent with a knowledge base | Infers from local percepts (breeze, snoring, glow) where the 3 pits, the soldier and the exit can be, and tells the player which cells are safe. |
| `palacio.py` | Bayesian agent | Keeps a probability distribution over the position of 3 traps, the soldier and the exit, updates it with Bayes' rule, draws heatmaps and recommends moves whose danger probability is below 0.1. |
| `river_mdp.py` | Markov decision process | Models the river crossing (stochastic current, islands) as an MDP, solves it with value iteration and simulates the optimal policy. |

In the two palace programs the **player** moves Willard and the agent acts as an assistant that shows what it has inferred; in the river program the agent computes and executes the policy itself. Every run generates a new random board or river.

## How to run

Python 3.12 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python kurtz.py        # part 1: logical agent (interactive)
python palacio.py      # part 2.1: Bayesian agent (interactive, opens heatmap windows)
python river_mdp.py    # part 2.2: MDP (non-interactive)
```

Controls in the palace programs: `W`/`A`/`S`/`D` to move, `G` to throw the grenade at an adjacent cell, `E` to leave the palace (only possible at the exit and after rescuing Kurtz).

## Method highlights

- **Logical agent.** The knowledge base keeps the visited cells, the history of percepts and the sets of possible positions of each hazard. Absence of a percept rules out all adjacent cells; a percept from a unique element (soldier, exit) restricts it to the adjacent cells, and evidence from several turns is intersected. Because three pits produce the same breeze, a pit is only confirmed when a breeze has a single remaining candidate cell.
- **Bayesian agent.** Each element has a 6×6 belief matrix with a uniform prior. Percepts give a deterministic likelihood, and visited cells are set to zero. Since the three traps are placed independently, the probability that a cell holds at least one trap is 1 − (1 − p_F)(1 − p_P)(1 − p_D); the soldier never shares a cell with a trap, so the danger probability is P(trap) + P(soldier).
- **MDP.** States are the non-island cells; the chosen move succeeds with probability 1 − (current strength of the column) and the current pushes the captain down otherwise; blocked moves keep him in place. Rewards are +100 at the exit (terminal state) and −1 per step, with γ = 0.95. Value iteration stops when no value changes by more than 10⁻⁶. Islands behave as obstacles.

Over 200 random rivers, value iteration converged in a median of 73 iterations (19–172), and the optimal policy reached the exit in a median of 13 steps (mean 16.9), with a median average reward of 86.9 over 10 simulated games.

## Repository structure

```
├── kurtz.py              # part 1: logical agent
├── palacio.py            # part 2.1: Bayesian agent
├── river_mdp.py          # part 2.2: MDP and value iteration
├── report/
│   ├── Memoria_Agentes_FIA.pdf   # report covering the three parts (Spanish)
│   ├── memoria.tex               # LaTeX source of the report
│   └── figs/
├── requirements.txt
└── README.md
```

## Limitations

- Boards and rivers are random and not guaranteed to be solvable (for example, pits can block the way to Kurtz).
- The palace agents advise a human player; they do not play on their own.
- The danger threshold (0.1) is fixed and conservative: a cell without any evidence has a danger probability of about 0.11–0.12, so it is never recommended.

## Changes made for publication

The original project was submitted as two separate reports (part 1 and part 2). For this repository:

- `palacio.py`: the trap risk was computed as the sum of the three trap distributions normalised over the board, which underestimated it about threefold (a cell with a 25% chance of fire was reported as safe). It is now the per-cell probability of at least one trap, and the danger combines it with the soldier as described above. The message shown when no move is safe now reports the least risky move and its probability instead of a fixed "50%".
- `river_mdp.py`: the exit is now treated as a terminal state in value iteration (before, its value grew to 2000 because the +100 reward was collected repeatedly) and convergence uses a tolerance of 10⁻⁶ instead of exact equality. The optimal policy is unchanged; the values and the number of iterations are now meaningful. The program also prints the number of iterations.
- `kurtz.py`: visited cells are no longer listed as possible exit locations.
- Student ID numbers were removed from the console banners, and the two reports were merged into a single, revised report.
