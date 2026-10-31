# Monopoly Game

A modern 2D digital board game built with Python and Pygame, featuring support for desktop play as well as browser execution via WebAssembly / Pygbag.

---

## Features

- **Classic & Modern Board Mechanics**:
  - 40 spaces including international city groups (Korea, Spain, Malaysia, South Africa, Russia, USA, India, Japan), Central Stations, Taxes, and Special card spaces.
  - Dedicated **Vacation Pot** badge displayed directly inside the Vacation corner tile ($Rs\text{ pot}$).
  - Progressive Station rent scaling ($25 \times 2^{n-1}$ for $n$ stations owned).
  - Monopoly group bonuses (doubled base rent for complete unbuilt color groups).
  - House and Hotel building progression up to 5 tiers per property with visual indicators on the board (`1H`–`4H`, `HOTEL`).
- **Interactive Settings & House Rules**:
  - **Player Count Selector**: Quickly choose between 2, 3, or 4 players before entering the lobby.
  - **Starting Money Dropdown**: Selectable initial funds (Rs 1,000, Rs 1,500, Rs 2,000, Rs 2,500).
  - **Color-Coded Toggle Switches**:
    - **Bank Loans**: Red when active (borrow Rs 500 at 15% interest due after 5 turns); grayscaled when OFF.
    - **Vacation Pot Jackpot**: Blue when active (collects 90% of paid taxes); grayscaled when OFF.
    - **House & Hotel Building**: Blue when active; grayscaled when OFF.
- **Multiplayer Lobby & Elimination**:
  - Support for 2 to 4 local players with customizable names and unique token colors.
  - Bankruptcy handling with debt settlement, asset transfers, and automatic game over / winner declaration.
- **Web & Desktop Ready**:
  - Async event loop compatible with Pygbag for compiling directly to WebAssembly and HTML5 canvas.

---

## Project Structure

- [main.py](main.py): Primary game source code containing data models (`Space`, `Player`), custom UI widgets (`Button`, `ToggleSwitch`, `Dropdown`), the state machine (`GameEngine`), and the async rendering loop.
- [build/web/index.html](build/web/index.html): Pygbag HTML5 canvas loader embedding the WebAssembly runtime.
- [build/version.txt](build/version.txt): Pygbag export configuration version.
- [.gitignore](.gitignore): Git ignore rules for virtual environments, OS metadata, and cache directories.

---

## Installation & Running Locally

### Prerequisites

- Python 3.10+
- Pygame 2.5+

### Setup

1. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Install dependencies** (if not already installed):
   ```bash
   pip install pygame
   ```

3. **Launch the game**:
   ```bash
   python main.py
   ```

---

## Building for the Web (Pygbag)

To rebuild or serve the WebAssembly version locally:

1. **Install pygbag**:
   ```bash
   pip install pygbag
   ```

2. **Build and test the web bundle**:
   ```bash
   pygbag --build main.py
   ```

3. Open the generated page in your browser at `http://localhost:8000`.

---

## Controls & Gameplay

- **Settings Screen**:
  - Choose player count (2, 3, or 4).
  - Pick Starting Money from the dropdown.
  - Toggle Loans, Vacation Pot, or Building on/off.
  - Click **GO TO LOBBY**.
- **Lobby**:
  - Customize player names by clicking a player card or typing and pressing **SET NAME** / Enter.
  - Click **START GAME** to begin.
- **Turn Actions**:
  - **ROLL**: Roll the dice to move across the board.
  - **BUY**: Purchase an unowned property when landing on it.
  - **BUILD**: Construct houses or hotels on owned complete color groups.
  - **LOAN**: Take a Rs 500 emergency loan if enabled in settings.
  - **END TURN**: Pass the turn to the next player.
