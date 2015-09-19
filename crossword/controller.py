import tkinter as tk
import string
import queue
from . import view as _view
from . import model as _model
from . import network as _network
from . import settings
from .constants import *


class Controller:

    def __init__(self):
        """Initialize a new controller, its network connection, and its
        sub-controllers."""
        # Queue and bindings
        self.queue = queue.Queue()
        self.bindings = {}
        # Get the player
        result = _view.join_dialog()
        if not result:
            quit()
        self.players = [_model.PlayerModel(result[0], result[1])]
        # Queue bindings
        self.bind(CLIENT_JOINED, self.on_client_joined)
        self.bind(ID_ASSIGNED, self.on_id_assigned)
        # Network connection
        self.connection = _network.CrosswordConnection(result[2])
        self.connection.queue(self.queue)
        self.connection.start()
        self.connection.emit(CLIENT_JOINED, {"name": self.players[0].name, "color": self.players[0].color})

        # Main contents
        self.view = _view.View()
        self.model = None
        # Sub-controllers
        self.header = HeaderController(self)
        self.puzzle = PuzzleController(self)
        self.clues = CluesController(self)
        # Hide
        self.view.hide()

    def reload(self):
        """Reload the controller."""
        self.header.reload()
        self.puzzle.reload()
        self.clues.reload()

    def load(self, model: _model.PuzzleModel):
        """Load the controller."""
        self.model = model
        self.header.load()
        self.puzzle.load()
        self.clues.load()
        # Clues also needs to be loaded for this to work
        self.puzzle.set_cell(0, 0)

    def update(self):
        """Update the controller."""
        if not self.queue.empty():
            event, data = self.queue.get()
            print(event)
            function = self.bindings.get(event)
            if function is None:
                print("caught event %s with no binding" % event)
            else:
                function(data)
        self.view.root.after(50, self.update)

    def main(self):
        """Run the crossword application."""
        self.update()
        self.view.main()
        self.connection.stop()

    def bind(self, event, function):
        self.bindings[event] = function

    def on_id_assigned(self, data):
        print(data)
        self.players[0].id = data

    def on_client_joined(self, data):
        print(data)
        if self.players[0].id != data["id"]:
            self.players.append(_model.PlayerModel(data["name"], data["color"]))
        else:
            self.view.root.title("Joined as %s" % self.players[0].name)


class SubController:

    def __init__(self, parent: Controller):
        """Initialize a new sub-controller."""
        self.parent = parent

    @property  # This is a property because the model is not permanent
    def model(self):
        """Get the model of the controller."""
        return self.parent.model

    @property  # This is a property because I'm unsure of how it will work
    def players(self):
        """Get the player of the controller."""
        return self.parent.players

    def reload(self):
        """Reload the controller."""
        pass


class HeaderController(SubController):

    def __init__(self, parent: Controller):
        super().__init__(parent)
        self.view = self.parent.view.header

    def load(self):
        self.view.title.set(self.model.title)
        self.view.author.set(self.model.author)

    reload = load


class PuzzleController(SubController):

    def __init__(self, parent: Controller):
        super().__init__(parent)
        self.view = self.parent.view.puzzle
        # Reference
        self.current = None
        # Bindings
        self.view.canvas.bind("<Button-1>", self.on_left_click)
        self.view.canvas.bind("<BackSpace>", self.on_backspace)
        self.view.canvas.bind("<space>", self.on_space)
        self.view.canvas.bind("<Tab>", self.on_tab)
        self.view.canvas.bind("<Shift-Tab>", self.on_shift_tab)
        self.view.canvas.bind("<Left>", self.on_arrow)
        self.view.canvas.bind("<Right>", self.on_arrow)
        self.view.canvas.bind("<Up>", self.on_arrow)
        self.view.canvas.bind("<Down>", self.on_arrow)
        self.view.canvas.bind("<Key>", self.on_key)
        self.view.canvas.focus_set()

    def load(self):
        d = settings.get("board:fill:default")
        e = settings.get("board:fill:empty")
        for cell in self.model.cells:
            cell.fill = d if cell.kind == LETTER else e
            self.draw(cell)

    reload = load

    def draw(self, model: (_model.CellModel, _model.WordModel, _model.PlayerModel), **options):
        if isinstance(model, _model.CellModel):
            self.view.canvas.delete(*list(model.drawings))
            x, y = model.x, model.y
            s = settings.get("board:cell-size")
            bbox = (x*s, y*s, (x+1)*s, (y+1)*s)
            model.drawings.box = self.view.canvas.create_rectangle(*bbox, fill=model.fill)
            if model.letters:
                h = s // 2 + 1
                pos = (x*s + h, y*s + h)
                letters = model.letters
                font = (settings.get("board:font-family"), int(s / (1.1 + 0.6*len(model.letters)))-3)
                color = model.color
                model.drawings.letters = self.view.canvas.create_text(*pos, text=letters, font=font, fill=color)
            if model.number:
                pos = (x*s + NUMBER_LEFT, y*s + NUMBER_TOP)
                number = model.number
                font = (settings.get("board:font-family"), int(s / 3.5)-2)
                model.drawings.number = self.view.canvas.create_text(*pos, text=number, font=font, anchor=tk.W)
        elif isinstance(model, _model.WordModel):
            for cell in model.cells:
                self.draw(cell)
        elif isinstance(model, _model.PlayerModel):
            # Ignore if the cell is empty
            cell = self.model.cells[model.x, model.y]
            if cell.kind == EMPTY:
                raise TypeError("Cannot select an empty cell")
            # If there is a selection, clear it
            if self.current:
                word = self.current.word[self.players[0].direction]
                word.fill = settings.get("board:fill:default")
                self.draw(word)
            # Change the fill of the word and selected cell
            if options.get("highlight") is not False:
                cell.word[self.players[0].direction].fill = settings.get("board:fill:selected")
                cell.fill = settings.get("board:fill:selected-letter")
            # Draw the word
            self.draw(cell.word[self.players[0].direction])
            # Set the current selection
            self.current = cell

    def switch_direction(self):
        word = self.current.word[self.players[0].direction]
        word.fill = settings.get("board:fill:default")
        self.draw(word)
        self.players[0].direction = [ACROSS, DOWN][self.players[0].direction == ACROSS]
        self.draw(self.players[0])
        self.parent.clues.set_clue(self.current.word[self.players[0].direction])

    def set_cell(self, x: int, y: int):
        self.players[0].x, self.players[0].y = x, y
        self.draw(self.players[0])
        self.parent.clues.set_clue(self.current.word[self.players[0].direction])
        self.view.canvas.focus_set()

    def move_cell(self, distance: int=1, absolute: bool=False):
        # Set constants for access
        step = -1 if distance < 0 else 1
        across = self.players[0].direction == ACROSS
        down = self.players[0].direction == DOWN
        x, y = self.current.x, self.current.y
        # Move while not complete
        while distance != 0:
            x += step * across
            y += step * down
            # Fix bound issues
            while not (0 <= x < self.model.width and 0 <= y < self.model.height):
                # Bounding rules
                if x < 0:
                    x = self.model.width - 1
                    y = (y - (not absolute)) % self.model.height
                elif x >= self.model.width:
                    x = 0
                    y = (y + (not absolute)) % self.model.height
                elif y < 0:
                    y = self.model.height - 1
                    x = (x - (not absolute)) % self.model.width
                elif y >= self.model.height:
                    y = 0
                    x = (x + (not absolute)) % self.model.width
            # Subtract the step if the new cell is a letter cell
            if self.model.cells[x, y].kind == LETTER:
                distance -= step
        # Select a new cell
        self.set_cell(x, y)

    def move_word(self, count=1):
        direction = self.players[0].direction
        index = (self.model.words[direction].index(self.current.word[direction]) + count)
        index %= len(self.model.words[direction])
        cell = self.model.words[direction][index].cells[0]
        self.set_cell(cell.x, cell.y)

    def insert_letter(self, letter: str):
        # If there is a current cell
        if self.current:
            self.current.owner = self.players[0]
            if letter == " ":
                self.current.letters = ""
            elif letter in string.ascii_lowercase:
                self.current.letters = letter.upper()
            elif letter in string.ascii_uppercase:
                self.current.letters += letter.upper()
            self.draw(self.current)

    def remove_letter(self):
        # If there is a current cell
        if self.current:
            self.current.letters = self.current.letters[:-1]
            self.draw(self.current)

    def on_left_click(self, event):
        # Get focus
        self.view.canvas.focus_set()
        # Efficiently access instance members
        s = settings.get("board:cell-size")
        x = (event.x - CANVAS_PAD - 1) // s
        y = (event.y - CANVAS_PAD - 1) // s
        cell = self.model.cells[x, y]
        # Ignore if the cell is empty
        if cell.kind == EMPTY:
            return
        # Change direction if the clicked cell is selected
        if cell == self.current:
            self.switch_direction()
        # Select the cell
        self.set_cell(x, y)

    def on_backspace(self, event):
        self.remove_letter()
        if settings.get("controls:on-backspace")[0] == "go to last cell":
            self.move_cell(-1)

    def on_space(self, event):
        on_space = settings.get("controls:on-space")[0]
        if on_space == "go to next cell":
            self.move_cell()
        elif on_space == "change direction":
            self.switch_direction()

    def on_tab(self, event):
        self.move_word(1)
        return "break"

    def on_shift_tab(self, event):
        self.move_word(-1)
        return "break"

    def on_arrow(self, event):
        on_arrow_key = settings.get("controls:on-arrow")[0]
        arrow_key_movement = settings.get("controls:arrow-movement")
        direction = ACROSS if event.keysym in ACROSS_ARROWS else DOWN
        distance = -1 if event.keysym in NEGATIVE_ARROWS else 1
        if self.players[0].direction != direction:
            self.switch_direction()
            if on_arrow_key == "switch direction and move":
                self.move_cell(distance=distance, absolute=arrow_key_movement == "absolute")
        elif on_arrow_key == "switch direction before moving":
            self.move_cell(distance=distance, absolute=arrow_key_movement == "absolute")

    def on_key(self, event):
        # If the key is a letter
        if event.keysym in string.ascii_letters:
            self.insert_letter(event.keysym)
            if event.keysym in string.ascii_lowercase:
                self.move_cell()


class CluesController(SubController):

    def __init__(self, parent: Controller):
        super().__init__(parent)
        self.view = self.parent.view.clues
        self.view.across_listbox.bind("<Button-1>", self.on_across_left_click)
        self.view.down_listbox.bind("<Button-1>", self.on_down_left_click)

    def load(self):
        self.view.across.set(list(map(lambda word: word.clue, self.model.words.across)))
        self.view.down.set(list(map(lambda word: word.clue, self.model.words.down)))

    reload = load

    def set_clue(self, word):
        if word in self.model.words.across:
            self.view.across_listbox.selection_clear(0, tk.END)
            index = self.model.words.across.index(word)
            self.view.across_listbox.selection_set(index)
            self.view.across_listbox.see(index)
        else:
            self.view.down_listbox.selection_clear(0, tk.END)
            index = self.model.words.down.index(word)
            self.view.down_listbox.selection_set(index)
            self.view.across_listbox.see(index)

    def on_across_left_click(self, event):
        index = self.view.across_listbox.nearest(event.y)
        cell = self.model.words.across[index].cells[0]
        if self.players[0].direction != ACROSS:
            self.parent.puzzle.switch_direction()
        self.parent.puzzle.set_cell(cell.x, cell.y)

    def on_down_left_click(self, event):
        index = self.view.down_listbox.nearest(event.y)
        cell = self.model.words.down[index].cells[0]
        if self.players[0].direction != DOWN:
            self.parent.puzzle.switch_direction()
        self.parent.puzzle.set_cell(cell.x, cell.y)
