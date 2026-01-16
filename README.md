# Block Buster (OOP Pygame)

Small Breakout-like game written in Python using Pygame. Uses OOP (classes for Paddle, Ball, Brick, and Game) and is intentionally similar in difficulty to a Pong-style project but different in gameplay.

Controls
- Left / Right arrows: move paddle
- Space: launch ball
- R: restart game after win/lose

Requirements
- Python 3.7+
- pygame (see `requirements.txt`)

Run
1. Create a virtual environment (recommended)
2. pip install -r requirements.txt
3. python main.py

Notes
- No external assets needed; the game draws simple colored rectangles and a circle.
- The code is in `main.py` and is structured to be easy to extend with power-ups, levels, and sounds.
