# TERMINAL GAME

version = "\033[94mv0.4\033[0m"

# init
import configparser
config = configparser.ConfigParser()
config.read('config.ini')

import cmd
import sys

from art import logo

import socket
import threading
import json

# game inits
from datetime import datetime

import ast
import math

import random
import hashlib

import time

from questions import questions
from rewards import rewards1

#init variables
username = config['UserData']['username']
debug = True
current = "mainMenu"
host = None

# debug func
def printbug(string):
    debugfont = f"\033[93m{string}\033[0m"
    print(str(debugfont))

# game funct
def generate_seed():
    """Generate a seed using a random integer, date, and time."""
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    seed_input = str(int(now)*random.randint(1,999))
    seed_hash = hashlib.md5(seed_input.encode()).hexdigest()
    return seed_hash[:16]

def generate_matrix(seed):
    """Generate a matrix."""
    random.seed(int(seed,16))

    allHexVals = list(range(256))
    random.shuffle(allHexVals)

    matrix = [f"{val:02x}" for val in allHexVals[:24]]

    if debug: printbug(seed)

    return matrix

def visualise_matrix(matrix, completedCells):
    """Visualise inputted matrix."""
    visualMatrix = matrix.copy()
    for i in range(len(visualMatrix)):
        if visualMatrix[i] in completedCells:
            visualMatrix[i] = "[\033[91mxx\033[0m]"
        else:
            visualMatrix[i] = f"[\033[92m{visualMatrix[i]}\033[0m]"

    print(*visualMatrix[0:6])
    print(*visualMatrix[6:12])
    print(*visualMatrix[12:18])
    print(*visualMatrix[18:24])

    if debug:   printbug(matrix);   printbug(completedCells);     

def generate_puzzle(seed, cellId):
    """Pull a question from the question pool and randomise contents."""
    random.seed(int(seed+cellId,16))

    selectedQuestion = random.choice(questions)
    if debug: printbug(selectedQuestion)

    a = random.randint(-99, 99)
    b = random.randint(1, 99)
    c = random.randint(1, 999)

    question = selectedQuestion["question"].format(a=a,b=b,c=c)
    answer = selectedQuestion["answer"](a,b,c)

    return {"question": question, "answer": answer, "weight": selectedQuestion["weight"]}

def setupTimer(terminal_instance):
    """Start timer"""
    duration = terminal_instance.current_game["setup_duration"]

    if debug: printbug(f"Starting timer for {duration}"); sys.stdout.write(terminal_instance.prompt); sys.stdout.flush()

    time.sleep(duration/2)
    print(f"{duration//2}s left until discovery!")
    sys.stdout.write(terminal_instance.prompt)
    sys.stdout.flush()

    time.sleep(duration/2)
    print("We've been discovered!")
    sys.stdout.write(terminal_instance.prompt)
    sys.stdout.flush()

    terminal_instance.current_game["phase"] = "standoff"

#       NETWORKING[]
def start_host_server(port=5000):
    """Start server socket and wait for client."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port))
    server.listen(1)
    print(f"Waiting for opponent on port {port}...")
    conn, addr = server.accept()
    p2name = conn.recv(4096).decode()
    print(f"{p2name} connected from {addr}!")
    return [conn, p2name]

def listen_for_messages(connection, terminal_instance, game_object):
    """Listen for all incoming messages (chat, updates, etc)"""
    connection.setblocking(False)

    if debug: 
        if not host: printbug("\r[LISTENER] Started listening..."); sys.stdout.write(terminal_instance.prompt); sys.stdout.flush()
        else: printbug("[LISTENER] Started listening...")

    buffer = b""
    while True:
        try:
            data = connection.recv(4096)
            
            if data:
                buffer += data
                if debug: printbug(f"[LISTENER] Received chunk: {len(data)} bytes")
                
                # Process complete messages (delimited by ||END||)
                while b"||END||" in buffer:
                    message, buffer = buffer.split(b"||END||", 1)
                    message = message.decode()
                    
                    if debug: printbug(f"[LISTENER] Processing: {message[:50]}")
                    
                    if message.startswith("CHAT:"):
                        chat_msg = message[5:]
                        print(f"\r{chat_msg}")
                        sys.stdout.write(terminal_instance.prompt)
                        sys.stdout.flush()
                    
                    elif message.startswith("GAME:"):
                        # listener game branch
                        opponent_data = json.loads(message[5:])

                        if not host:
                            opponent_data["p1"], opponent_data["p2"] = opponent_data["p2"], opponent_data["p1"]

                        if not hasattr(terminal_instance, 'current_game'):
                            terminal_instance.current_game = {}
                        terminal_instance.current_game = opponent_data

                        threading.Thread(target=setupTimer, args=(terminal_instance,), daemon=True).start()
                        if debug: printbug("Started timer!")
                        
                        global current; current = "playing"     
                        print("Game started!")

                        print(f"\033[94m{terminal_instance.current_game["p2"]["name"]}\033[0m's matrix")
                        visualise_matrix(terminal_instance.current_game["p1"]["matrix"], terminal_instance.current_game["p1"]["cellsHacked"])

                        sys.stdout.write(terminal_instance.prompt)
                        sys.stdout.flush()

                    elif message.startswith("UPDATE:"):
                        update = json.loads(message[7:])
                        if debug: printbug(f"Received: {update}")

                        game = terminal_instance.current_game
                        game["p2"]["cellsHacked"], game["p2"]["utils"] = update[0], update[1]

                        sys.stdout.write(terminal_instance.prompt)
                        sys.stdout.flush()


        except ConnectionResetError:
            if debug: printbug("[LISTENER] Connection reset by host")
            break
        
        except Exception as e:
            if isinstance(e, BlockingIOError): 
                time.sleep(0.01)
                continue

            if debug: printbug(f"[LISTENER] Error: {type(e).__name__}: {e}")
            break

def receive_game(client, terminal_instance):
    """Start listeners"""
    if debug: printbug("[RECEIVE_GAME] Starting listener thread...")
    thread = threading.Thread(target=listen_for_messages, args=(client, terminal_instance, None), daemon=True)
    thread.start()
    
    global current
    current = "intermission"

# all the juicy stuff below
class terminal(cmd.Cmd):
    print("Successfully loaded!")
    prompt = "\033[93m>\033[0m "

    def __init__(self):
        #this runs automatically when the terminal starts
        super().__init__()
        self.cell_cooldowns = {}
        self.wrongAttempts = 0

        print("\033[H\033[J", end="")
        
        global current
        print(logo)
        print(f"{version}\n")

        if username != "":
            self.intro = f"Welcome back to the terminal, \033[93m{username}\033[0m.\n Type ? or help for a list of commands."
        else: 
            self.intro = "It seems like this is your first time inside the terminal.\n Please enter a new name using [setUsername]."

    def precmd(self, line):
        """Called before command execution"""
        words = line.split()
        if current == "solving" and words and words[0] not in ("c", "chat"):
            self.default(line)
            return ""
        return line

    def emptyline(self):
        return False

    def do_setUsername(self, arg):
        """Sets username.
        Usage: setUsername [username]"""
        if not current == "mainMenu":
            print("You are not allowed to change your username right now!")
            return

        if arg:
            if " " in arg:
                print("Spaces aren't allowed inside a username.")
                return

            global username
            username = f"{arg}"

            config["UserData"]['username'] = f"{arg}"
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            print(f"Username set to {username}!")
        else:
            print("Incorrect syntax, use: setUsername [username]")

    #       NETWORKING

    def do_host(self, arg):
        """Start hosting server, wait for opponent.
        Usage: host"""

        global current, host; 
        if current != "mainMenu":
            print("You cannot host unless in the main menu!")
            return
        
        hostServerValues = start_host_server()
        self.opponent_connection = hostServerValues[0]
        self.p2name = hostServerValues[1]
        print(" Opponent connected, waiting for [startgame]...")

        thread = threading.Thread(target=listen_for_messages, args=(self.opponent_connection, self, None), daemon=True)
        thread.start()

        current = "intermission"; host = True

    def do_join(self, arg):
        """Connect to host game.
        Usage: join [host_ip]"""
        global current, username, host

        if not arg:
            print("Incorrect syntax, use: join [host_ip]")     
            return
        else: 
            ip = arg    
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ip, 5000))
        client.send(username.encode())

        self.opponent_connection = client
        print(f"Joined {ip}!\nWaiting for host to start game...")

        host = False

        thread = threading.Thread(target=receive_game, args=(client, self), daemon=True)
        thread.start()

        current = "intermission"

    def do_chat(self, arg):
        if not arg:
            print("Incorrect syntax, use: chat [message]")
            return

        message = f"CHAT:\033[94m{username}\033[0m: {arg}||END||"
        if debug: printbug(f"[CHAT] Sending: {message}")
        self.opponent_connection.send(message.encode())

    def send_update(self, data):
        message = "UPDATE:" + json.dumps(data) + "||END||"
        self.opponent_connection.send(message.encode())

    # gameplay stuff

    def default(self, line):
        """Handle answer submissions during solving phase."""
        global current
        if current != "solving":
            print(f"Unknown command: {line}")
            return

        try:
            value = float(line)
        except ValueError:
            print("Cannot use that right now.")
            return     
        
        if value == self.current_puzzle["answer"]:
            print("Cell hacked successfully!")

            seed = self.current_game["p1"]["seed"]
            random.seed(int(seed+self.current_cell, 16))

            if self.current_puzzle["weight"] == 1:
                reward = rewards1[random.randint(0,len(rewards1)-1)]
                self.current_game["p1"]["utils"].append(reward)
                print(f"Stole {reward} from matrix!")

            self.current_game["p1"]["cellsHacked"].append(self.current_cell)

            packageToSend = [self.current_game["p1"]["cellsHacked"], self.current_game["p1"]["utils"]]
            self.send_update(packageToSend)

            visualise_matrix(generate_matrix(seed), self.current_game["p1"]["cellsHacked"])

            current = "playing"
        else:
            self.wrongAttempts += 1
            
            if 3 - self.wrongAttempts == 0:
                print(f"You've been kicked out of [\033[94m{self.current_cell}\033[0m]!")
                self.cell_cooldowns[self.current_cell] = time.time() + 15
                current = "playing"
            else:
                print(f"Wrong answer. {3-self.wrongAttempts} attempts left.")

    def do_c(self, arg):
        """Calculator function, only supports one operation at a time.
        Usage: c [calculation]"""
        try: 
            tree = ast.parse(arg, mode="eval")
            count = sum(isinstance(node, ast.BinOp) for node in ast.walk(tree))
            if count > 1:
                print("Only one operation is allowed at a time!")
                return

            result = eval(arg, {"__builtins__": {}}, {"math": math})
            print(result)
        except:
            print("Invalid calculation.")

    def do_hack(self, arg):
        #           hack funcc
        """Hack opponent's matrix cell, cannot be used unless inside a game.
        Usage: hack [cell id]"""
        global current
        if current != "playing":   
            if current == "solving":
                print("Cannot use hack right now.")
                return
            print("Hack cannot be used unless playing!")
            return

        arg = arg.strip("[]")

        matrix = self.current_game["p1"]["matrix"]
        hackedCells = self.current_game["p1"]["cellsHacked"]
        seed = self.current_game["p1"]["seed"]

        if arg not in matrix:
            print(f"Cell [{arg}] not found in matrix!")
            return
                
        if arg in hackedCells:
            print("You've already hacked this cell!")
            return

        if arg in self.cell_cooldowns:
            if time.time() < self.cell_cooldowns[arg]:
                print(f"You cannot hack this cell for another {round(self.cell_cooldowns[arg]-time.time())} seconds!")
                return

        self.wrongAttempts = 0

        print(f"Hacking [\033[92m{arg}\033[0m]...")
        time.sleep(random.randint(0,2))

        puzzle = generate_puzzle((seed), arg)
        self.current_puzzle = puzzle
        print(puzzle["question"])

        self.current_cell = arg
        current = "solving"

    def do_matrix(self, arg):
        """Show the matrix you are currently hacking."""
        if current != "playing": 
            print("Matrix cannot be used unless playing!")
            return
        p2name = self.current_game["p2"]["name"]
        matrix = self.current_game["p1"]["matrix"]
        completedCells = self.current_game["p1"]["cellsHacked"]

        print(f"{p2name}'s matrix")
        visualise_matrix(matrix, completedCells)

    #       scary startgame below (be careful)

    def do_startgame(self, arg):
        """Creates everything necessary for the game to start."""
        global current

        if current != "intermission":
            print("Cannot start game unless in intermission!")
            return

        if not hasattr(self, 'opponent_connection'):
            print("No opponent connected!")
            return

        if not host: 
            print("Only the host can start the game!")
            return

        p1seed = generate_seed()
        p2seed = generate_seed()

        p1name = username

        current = "playing"

        game = {
            "p1": {
                "name": p1name,
                "seed": p1seed,
                "matrix": generate_matrix(p1seed),
                "cellsHacked": [],
                "utils": [],
                "isHost": True
            },
            "p2": {
                "name": self.p2name,
                "seed": p2seed,
                "matrix": generate_matrix(p2seed),
                "cellsHacked": [],
                "utils": []
            },
            "phase": "setup",
            "start_time": datetime.now().isoformat(),
            "setup_duration": 120,
            "final_duration": 60,
            "isHost": False
        }

        self.current_game = game
        threading.Thread(target=setupTimer, args=(self,), daemon=True).start()

        try:
            game_json = json.dumps(game)
            self.opponent_connection.send(("GAME:"+game_json+"||END||").encode())
            if debug: printbug("Game sent successfully!")

            print("Game started!")

            print(f"\033[94m{game["p2"]["name"]}\033[0m's matrix")
            visualise_matrix(game["p1"]["matrix"], game["p1"]["cellsHacked"])
        except Exception as e:
            if debug: printbug(f"[STARTGAME] Send error: {e}") 

    #       Debug[] 

    def do_print(self, arg):
        # find variables
        """Prints the specified variable's value."""
        variables = {
            "username": username,
            "current": current,
            "wins": config['UserData']['wins'],
            "losses": config['UserData']['losses'],
            "debug": debug,
            "host": host,
        }
        gameVariables = {
            "seed": self.current_game["p1"]["seed"],
            "util": self.current_game["p1"]["utils"],
            "phase": self.current_game["phase"]
        }
        if arg in variables:        
            print(variables[arg])
        elif arg in gameVariables and current == "playing":
            print(gameVariables[arg])
        else:
            print(f"Variable [{arg}] not found.")

    def do_makeAseed(self, arg):
        """Creates a seed."""
        seed = generate_seed()
        print(seed)

    def do_makeAmatrix(self, arg):
        """Creates a matrix.
        Usage: makeAmatrix [seed] [completedCells]"""
        if not arg:
            matrix = generate_matrix(generate_seed())
            visualise_matrix(matrix, [])
            return
        
        parts = arg.split(maxsplit = 1)
        
        if len(parts) == 1:
            completed = []
        else:
            completed = parts[1].split()
        
        matrix = generate_matrix(parts[0])
        visualise_matrix(matrix, completed)

    def do_makeApuzzle(self, arg):
        """Creates a puzzle.
        Usage: makeApuzzle [seed] [cell_id]"""
        if not arg:
            seed = generate_seed()
            generate_puzzle(seed, [])
            return
        
        parts = arg.split(maxsplit = 1)
        
        if len(parts) == 1:
            print("Incorrect syntax, use makeApuzzle [seed] [cell_id]")
            return

        generate_puzzle(parts[0], parts[1])


    #misc

    def do_clear(self, arg):
        """Clears the terminal screen."""
        print("\033[H\033[J", end="")

    def do_exit(self, arg):
        """Exits the terminal."""
        print("Exiting...")
        return True  # Returning True stops the loop and exits

if __name__ == "__main__":
    terminal().cmdloop()