"""Crossword application model.

Contains all containers and models used in the crossword application.
"""

# Import
import puz
from crossword.constants import *


# Convenience
def to_position(i: int, w: int) -> tuple:
    """Turn an index and width into a position."""
    y, x = divmod(i, w)
    return x, y


def to_index(x: int, y: int, w: int) -> int:
    """Turn a position and width into an index."""
    return y*w + x


class DrawingsModel:
    """Basic container class for a canvas drawing group."""

    def __init__(self):
        """Initialize the canvas drawing group."""
        self._ = []

    def __setattr__(self, key, value):
        """Set and track an attribute of the drawing group."""
        super().__setattr__(key, value)
        self._.append(key)

    def __iter__(self):
        """Get all indices of the drawings in the model."""
        return iter([item for item in self._ if item is not None])


class DualWordAccess:
    """Easy access to cell words."""

    def __init__(self):
        """Initialize a dual word access."""
        self.across = None
        self.down = None

    def __getitem__(self, key):
        """Conveniently access the elements of the access."""
        return {ACROSS: self.across, DOWN: self.down}[key]


class CellModel:
    """Basic container class for a single old cell."""

    def __init__(self, x: int, y: int, kind: str, solution: str):
        """Initialize a crossword cell container."""
        # Set by fill and solution
        self.x = x
        self.y = y
        self.kind = kind
        self.word = DualWordAccess()
        self.solution = solution
        # Changeable
        self.letters = ""
        self.owner = None
        # Constant
        self.number = ""
        self.fill = "white"
        # Drawing
        self.drawings = DrawingsModel()
        self.drawings.box = None
        self.drawings.number = None
        self.drawings.letter = None

    def update(self, **options):
        """Update the cells attributes."""
        for option in options.items():
            setattr(self, *option)


class CellsAccess:
    """Basic matrix-like container for a old board's cells."""

    def __init__(self, puzzle: puz.Puzzle):
        """Initialize a crossword cells container."""
        self._width = puzzle.width
        self.cells = []
        # Create the cells
        zipped = list(zip(puzzle.fill, puzzle.solution))
        for y, row in enumerate(zipped[i:i+puzzle.width] for i in range(0, len(zipped), puzzle.width)):
            for x, (kind, solution) in enumerate(row):
                self.cells.append(CellModel(x, y, kind, solution))

    def __getitem__(self, position: (int, tuple)):
        """Get a cell with its coordinate position."""
        if isinstance(position, int):
            return self.cells[position]
        elif isinstance(position, tuple) and len(position) == 2:
            return self.cells[to_index(position[0], position[1], self._width)]

    def __iter__(self):
        """Iterate through the cells in the access."""
        return iter(self.cells)

    def __len__(self):
        """Get the number of cells in the access."""
        return len(self.cells)


class WordModel:
    """Basic container class for a single old cell."""

    def __init__(self, direction: str, number: int, clue: int):
        """Initialize a crossword cell container."""
        # Basic word data
        self.direction = direction
        self.number = number
        self.clue = clue
        self.cells = []

    def update(self, **options):
        """Mass update the cells in the word."""
        for cell in self.cells:
            cell.update(**options)


class WordsAccess:
    """Basic container for a list of words."""

    def __init__(self, puzzle: puz.Puzzle, cells: CellsAccess):
        """Initialize a crossword words container."""
        self.words = []
        self.across = []
        self.down = []
        # Load the words
        numbering = puzzle.clue_numbering()
        for info in numbering.across:
            x, y = to_position(info["cell"], puzzle.width)
            linked = list(map(lambda j: cells[x+j, y], range(info["len"])))
            word = WordModel(ACROSS, info["num"], info["clue"])
            # Link the word and cells
            word.cells = linked
            for cell in linked:
                cell.word.across = word
            word.cells[0].number = word.number
            # Add the word to the lists
            self.words.append(word)
            self.across.append(word)
        for info in numbering.down:
            x, y = to_position(info["cell"], puzzle.width)
            linked = list(map(lambda j: cells[x, y+j], range(info["len"])))
            word = WordModel(DOWN, info["num"], info["clue"])
            # Link the word and cells
            word.cells = linked
            for cell in linked:
                cell.word.down = word
            word.cells[0].number = word.number
            # Add the word to the lists
            self.words.append(word)
            self.down.append(word)

    def __iter__(self):
        """Iterate through the words in the access."""
        return self.words

    def __len__(self):
        """Get the number of words in the access."""
        return len(self.words)

    def __getitem__(self, key):
        """Conveniently get the across or down word list."""
        return {ACROSS: self.across, DOWN: self.down}[key]


class PuzzleModel:
    """Basic container class for a single old cell."""

    def __init__(self, puzzle: puz.Puzzle):
        """Initialize a crossword cell container with a puzzle."""
        # Basic puzzle data
        self.title = puzzle.title
        self.author = puzzle.author
        self.copyright = puzzle.copyright
        self.notes = puzzle.notes
        self.postscript = puzzle.postscript
        self.width = puzzle.width
        self.height = puzzle.height
        self.version = puzzle.version
        # Cells and words
        self.cells = CellsAccess(puzzle)
        self.words = WordsAccess(puzzle, self.cells)


class PlayerModel:
    """Basic player profile model."""

    def __init__(self, name: str, color: str):
        """Initialize a player profile model."""
        self.custom = {}
        # Defined by server
        self.id = 0
        # Already set
        self.direction = ACROSS
        self.x = 0
        self.y = 0

    def __repr__(self):
        return str(self.id)

    def update(self, **options):
        self.custom.update(options)

    def get(self, item, default=None):
        return self.custom.get(item, default)

    def __getitem__(self, item):
        return self.custom.get(item, None)

    def __setitem__(self, key, value):
        self.custom[key] = value
