# terminal-game
PvP LAN puzzle game run inside the terminal.

## Gameplay
Each player has a grid of two-digit hexadecimal cells. You break into your opponent’s grid by solving puzzles, then fight to patch the holes they left in yours.

**Infiltration**

Use `matrix` to view the grid you’re attacking, then `hack [cell]` to start hacking a cell.

Each cell holds a math or logic puzzle. Type the answer to break in.
Successfully hacking a cell rewards you with software (powerup) you can use during lockdown phase.
Incorrectly answering three times in a row locks you out of the cell for 15 seconds.

You are equipped with a calculator that can only do one operation at a time. You may use it at any time. Usage: `c [calculation]`

**Lockdown**

When the timer ends, the roles flip. Every hole you made is now a target for your opponent to patch, and every hole they made in your grid is yours to fix.

Patch their holes by solving puzzles and fixing whatever damage they caused.
Use your software to protect your own holes from being patched or aid you in patching the holes your opponent made.

**Winning**

You can win in two ways:

Time, whoever has the highest score before time runs out wins. Score counts holes made, holes patched, holes left standing, and unused software.

First to patch all holes, patching all the holes your opponent made before they patched yours. Score is still counted, but has no effect on who won.

## How to play
Run launch.py, you should see the terminal open.
If you are a new user, it will prompt you to make a new username, use `setUsername` then whatever username you want, example: `setUsername ExtrapolatedFrame`

**Hosting:**

Use `host`, and it will start waiting for a connection.
Once a player joins, use `startgame` to start the game.

**Joining**

Use `join [ip]`, ip being the ip of the host's computer.
