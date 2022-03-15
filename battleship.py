from tkinter import *
from tkinter import font
import random

print("Initializing...")

sysrand = random.SystemRandom()
seed = None
GAME_SIZE = 500  # Высота игрового окна в пикселях
GRID_SIZE = 10  # Размер игрового поля
GRID_LETTERS = [char for char in "ABCDEFGHIJ"]
MAX_PLAYERS = 2
SHIP_LENGTHS = [4, 3, 3, 2, 2, 2]
QUEUE_BLOCK_SIZE = 16


def _create_circle(self, x, y, r, **kwargs):
    return self.create_oval(x - r, y - r, x + r, y + r, **kwargs)


Canvas.create_circle = _create_circle


class Main(object):
    def __init__(self, master):
        super(Main, self).__init__()

        self.frame = Frame(master)
        self.frame.pack(fill=BOTH, expand=1)

        self.canvas = Canvas(self.frame, width=int(GAME_SIZE / 2), height=GAME_SIZE)
        self.canvas.pack(fill=BOTH, expand=1)
        self.canvas.config(highlightbackground="black", highlightthickness=2)
        self.canvas_placement_queue = Canvas(self.frame, width=int(GAME_SIZE / 2),
                                             height=(len(SHIP_LENGTHS) * QUEUE_BLOCK_SIZE))
        self.canvas_placement_queue.pack(fill=Y)

        self.grid_block_height = 10
        self.grid_block_width = 10
        self.current_mouse_over_grid = None

        self.game_phase = "setup"  # Возможные значения: setup, battle, end
        self.boat_rotation = False  # Правда - вертикальное положение, Ложь - горизонтальное
        self.selected_ship_index = None

        self.canvas.bind("<Motion>", self.onMouseMove)
        self.canvas.bind("<Button-1>", self.onGridClick)
        self.canvas.bind("<Button-3>", self.onGridRightClick)
        self.canvas_placement_queue.bind("<Motion>", self.onPlacementQueueMouseMove)
        self.canvas_placement_queue.bind("<Button-1>", self.onPlacementQueueClick)
        self.reset()

    def reset(self):
        self.canvas_placement_queue.pack(fill=Y)

        self.grid_player1 = []
        self.grid_player2 = []
        self.boat_placement_queue = SHIP_LENGTHS.copy()
        for r in range(GRID_SIZE):
            self.grid_player1 += [[]]
            self.grid_player2 += [[]]
            for c in range(GRID_SIZE):
                self.grid_player1[r] += [None]
                self.grid_player2[r] += [None]

        print("Game reset")

    def draw(self):
        self.canvas.delete(ALL)
        self.grid_block_height = int(self.canvas.winfo_height() / 2 / GRID_SIZE)
        self.grid_block_width = int(self.canvas.winfo_width() / GRID_SIZE)

        boat_placement, boat_placement_valid = self.getSelectedShipPlacement()
        for p in range(MAX_PLAYERS, 0, -1):
            for y in range(int(GAME_SIZE / 2 * (p - 1)) - 1, int(GAME_SIZE / 2 * p) + 1, self.grid_block_height):
                for x in range(0, int(GAME_SIZE / 2) + 1, self.grid_block_width):
                    self.canvas.create_rectangle(x, y, x + self.grid_block_width, y + self.grid_block_height)

                    grid_pos = self.getGridPos(x, y)
                    try:
                        grid_space_content = self.getGridSpaceContent(*grid_pos)
                    except Exception as e:
                        continue
                    circle_color = None
                    if grid_space_content:
                        if grid_space_content == "boat":
                            circle_color = "dark gray"
                    if self.current_mouse_over_grid and self.current_mouse_over_grid == grid_pos:
                        if self.game_phase == "setup":
                            if self.current_mouse_over_grid[0] == 1:
                                circle_color = "lime green"
                            else:
                                circle_color = "dark red"
                        elif self.game_phase == "battle":
                            if self.current_mouse_over_grid[0] == 2:
                                circle_color = "lime green"
                            else:
                                circle_color = "dark red"
                    elif self.game_phase == "setup":
                        if boat_placement and grid_pos in boat_placement:
                            if boat_placement_valid:
                                circle_color = "light gray"
                            else:
                                circle_color = "dark red"
                    elif self.game_phase == "battle":
                        if grid_space_content:
                            if grid_space_content == "hit":
                                circle_color = "red"
                            elif grid_space_content == "miss":
                                circle_color = "white"
                    if circle_color:
                        grid_center = self.getGridSpaceCenter(*grid_pos)
                        radius = int(min(self.grid_block_width, self.grid_block_height) / 4)
                        radius = max(3, radius)
                        self.canvas.create_circle(*grid_center, radius, fill=circle_color)

        # линия между игровыми полями
        self.canvas.create_line(0, int(GAME_SIZE / 2), int(GAME_SIZE / 2), int(GAME_SIZE / 2), width=4)

    def draw_placement_queue(self):
        self.canvas_placement_queue.delete(ALL)
        if self.game_phase == "setup":
            # draw boat placement queue
            radius = int(QUEUE_BLOCK_SIZE / 2) - 2
            for y, boat_length in zip(range(len(self.boat_placement_queue)), self.boat_placement_queue):
                for x in range(boat_length):
                    self.canvas_placement_queue.create_circle((x * QUEUE_BLOCK_SIZE) + radius + 2,
                                                              (y * QUEUE_BLOCK_SIZE) + radius + 2, radius, fill="gray")

            # indicate which boat is selected
            if self.selected_ship_index is not None:
                selection_width = QUEUE_BLOCK_SIZE * self.boat_placement_queue[self.selected_ship_index]
                basey = QUEUE_BLOCK_SIZE * self.selected_ship_index
                self.canvas_placement_queue.create_rectangle(0, basey, selection_width, basey + QUEUE_BLOCK_SIZE,
                                                             outline="red")

    def onMouseMove(self, event):
        if self.current_mouse_over_grid != self.getGridPos(event.x, event.y):
            self.current_mouse_over_grid = self.getGridPos(event.x, event.y)
        self.draw()

    def onPlacementQueueMouseMove(self, event):
        self.draw_placement_queue()

    def onPlacementQueueClick(self, event):
        index = event.y // QUEUE_BLOCK_SIZE
        if index < len(self.boat_placement_queue):
            self.selected_ship_index = index
        else:
            self.selected_ship_index = None

        self.draw_placement_queue()

    def onGridClick(self, event):
        if self.game_phase == "setup":
            # place boat
            boat_placement, isValid = self.getSelectedShipPlacement()
            if isValid:
                for pos in boat_placement:
                    self.setGridSpaceContent(*pos, "boat")
                del self.boat_placement_queue[self.selected_ship_index]
                if self.selected_ship_index >= len(self.boat_placement_queue):
                    self.selected_ship_index -= 1
                if len(self.boat_placement_queue) == 0:
                    self.selected_ship_index = None
                    self.canvas_placement_queue.pack_forget()
                    self.game_phase = "battle"
                    self.aiThinkSetup()
                    print("Setup phase complete")
                self.draw_placement_queue()
        elif self.game_phase == "battle":
            attack_pos = self.getGridPos(event.x, event.y)
            if attack_pos[0] == 2:
                self.takeTurn(*attack_pos)
                self.aiThinkTurn()
            winner = self.getWinner()
            if winner:
                self.onWinner(winner)

        self.draw()

    def onGridRightClick(self, event):
        if self.game_phase == "setup":
            # rotate boat placement
            self.boat_rotation = not self.boat_rotation
        self.draw()

    def onWinner(self, winner):
        self.game_phase = "end"

    def getGridPos(self, canvas_x, canvas_y):
        for p in range(MAX_PLAYERS, 0, -1):
            y_base = int(GAME_SIZE / 2 * (p - 1))
            for k in range(y_base, y_base + int(GAME_SIZE / 2), self.grid_block_height):
                for h in range(0, int(GAME_SIZE / 2) + 1, self.grid_block_width):
                    if (h <= canvas_x <= h + self.grid_block_width) and (
                            k <= canvas_y <= k + self.grid_block_height):
                        return MAX_PLAYERS - p + 1, int(h / self.grid_block_width), int(k / self.grid_block_height) - (
                                (p - 1) * GRID_SIZE)

    def setGridSpaceContent(self, player_num, grid_x, grid_y, content):
        if player_num == 1:
            self.grid_player1[grid_y][grid_x] = content
        elif player_num == 2:
            self.grid_player2[grid_y][grid_x] = content

    def getGridSpaceContent(self, player_num, grid_x, grid_y):
        if player_num == 1:
            return self.grid_player1[grid_y][grid_x]
        elif player_num == 2:
            return self.grid_player2[grid_y][grid_x]

    def getGridSpaceCenter(self, player_num, grid_x, grid_y):
        _p = MAX_PLAYERS - player_num
        base_x = grid_x * self.grid_block_width
        base_y = grid_y * self.grid_block_height + _p * (GAME_SIZE / 2)
        return int(base_x + (self.grid_block_width / 2)), int(base_y + (self.grid_block_height / 2))

    def getShipPlacement(self, player_num, start_pos, ship_length, vertical):
        c = []
        positions = []
        isValid = None
        if vertical:
            # X будет константой
            c = [start_pos[1]] * ship_length
            positions = zip(c, range(start_pos[2], start_pos[2] + ship_length))
            isValid = start_pos[2] + ship_length <= GRID_SIZE
        else:
            # Y будет константой
            c = [start_pos[2]] * ship_length
            positions = zip(range(start_pos[1], start_pos[1] + ship_length), c)
            isValid = start_pos[1] + ship_length <= GRID_SIZE

        positions = list(positions)
        # prepend the player numbers
        for i in range(len(positions)):
            positions[i] = (start_pos[0],) + positions[i]

        if isValid:
            for pos in positions:
                if self.getGridSpaceContent(*pos) is not None:
                    isValid = False

        return positions, start_pos[0] == player_num and isValid

    def getSelectedShipPlacement(self):
        """
        Возвращает кортеж, состоящий из позиции корабля и логического значения, отображающего положение корабля в
        плоскости.
        """
        if not self.current_mouse_over_grid or self.selected_ship_index is None:
            return None, False
        if not self.boat_placement_queue or len(self.boat_placement_queue) == 0:
            return None, False

        return self.getShipPlacement(1, self.current_mouse_over_grid,
                                     self.boat_placement_queue[self.selected_ship_index], self.boat_rotation)

    def takeTurn(self, player_num, grid_x, grid_y):
        if not self.getGridSpaceContent(player_num, grid_x, grid_y) is None and not self.getGridSpaceContent(player_num,
                                                                                                             grid_x,
                                                                                                             grid_y) \
                                                                                    == "boat":
            return

        attacking_player = None
        if player_num == 1:
            attacking_player = 2
        elif player_num == 2:
            attacking_player = 1
        content = None
        if self.getGridSpaceContent(player_num, grid_x, grid_y) == "boat":
            content = "hit"
        else:
            content = "miss"
        self.setGridSpaceContent(player_num, grid_x, grid_y, content)
        print("Player {} {} Player {} at {}{}".format(attacking_player, content, player_num, GRID_LETTERS[grid_y],
                                                      grid_x))

    def aiThinkSetup(self):
        # расставление кораблей компьютером
        print("Setting up ai ships...")
        for ship in SHIP_LENGTHS:
            while True:
                vertical = bool(random.getrandbits(1))
                x, y = None, None
                if vertical:
                    x = random.randrange(0, GRID_SIZE)
                    y = random.randrange(0, GRID_SIZE - ship)
                else:
                    x = random.randrange(0, GRID_SIZE - ship)
                    y = random.randrange(0, GRID_SIZE)
                if self.getGridSpaceContent(*(2, x, y)) == "boat":
                    continue
                boat_placement, isValid = self.getShipPlacement(2, (2, x, y), ship, vertical)
                if isValid:
                    for pos in boat_placement:
                        self.setGridSpaceContent(*pos, "boat")
                    break

    def aiThinkTurn(self):
        def _getAdjacent(grid_x, grid_y):
            adjacent = [
                (1, grid_x - 1, grid_y),
                (1, grid_x, grid_y - 1),
                (1, grid_x + 1, grid_y),
                (1, grid_x, grid_y + 1),
            ]
            to_remove = []
            for i in range(len(adjacent)):
                if adjacent[i][1] < 0 or adjacent[i][1] >= GRID_SIZE or adjacent[i][2] < 0 or adjacent[i][2] \
                        >= GRID_SIZE:
                    to_remove += [i]
            to_remove = sorted(to_remove, reverse=True)
            for index in to_remove:
                del adjacent[index]
            return adjacent

        # проверяет все соседние клетки после попадания по кораблю
        for y in range(len(self.grid_player1)):
            for x in range(len(self.grid_player1[y])):
                if self.getGridSpaceContent(1, x, y) == "hit":
                    adjacent = _getAdjacent(x, y)
                    for pos in adjacent:
                        if self.getGridSpaceContent(*pos) not in ["hit", "miss"]:
                            self.takeTurn(*pos)
                            return

        # стреляет
        for y in range(len(self.grid_player1)):
            for x in range(len(self.grid_player1[y])):
                if y % 2 == x % 2 and self.getGridSpaceContent(1, x, y) not in ["hit", "miss"]:
                    self.takeTurn(1, x, y)
                    return

    def getWinner(self):
        # возвращает номер победителя

        def areAllShipsSunk(grid):
            areShipsSunk = True
            for row in grid:
                if "boat" in row:
                    areShipsSunk = False
            return areShipsSunk

        if areAllShipsSunk(self.grid_player1):
            return 2
        elif areAllShipsSunk(self.grid_player2):
            return 1
        else:
            return None


root = Tk()
root.title("BattleShip vs AI")
arial14 = font.Font(family="Arial", size=14)
ubuntuMono10 = font.Font(family="Ubuntu Mono", size=10)
app = Main(root)

# app.draw()

root.mainloop()
