"""The Main Crossword Application Interface.

View serves as the graphical component in crossword. Instantiating a
`View` object spawns and loads a new crossword application. This
application must be the main thread, as tkinter is not thread-safe.
"""


# Data
__author__ = "Noah Kim"
__version__ = "0.2.0"
__status__ = "Development"


# Import
import tkinter as tk
from . import settings
from .constants import *


# Application
class View:
    """The main crossword application interface."""

    def __init__(self):
        """Initialize a new crossword application."""
        # Root window
        self.root = tk.Tk()
        self.root.title("Crossword")
        # Padding frame
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill="both", padx=PAD, pady=PAD)
        # Initialize widget groups
        self.header = HeaderView(self.root, self.frame)
        self.puzzle = PuzzleView(self.root, self.frame)
        self.clues = CluesView(self.root, self.frame)
        # Show widgets
        self.header.show()
        self.puzzle.show()
        self.clues.show()

    def main(self):
        """Run the main loop of the view."""
        self.header.title.set("Hello, world!")
        self.header.author.set("Noah Kim")
        self.puzzle.clue.set("This is a clue")
        self.puzzle.time.set("00:00:00")
        self.root.mainloop()

    def stop(self):
        """Stop the view during the main loop."""
        self.root.quit()


class GroupView:
    """Parent class for a crossword application widget group."""

    def __init__(self, root, parent):
        """Build the widget group."""
        self.root = root
        self.parent = parent
        # Content frame
        self.frame = tk.Frame(self.parent)
        # Reference
        self.loaded = False
        self.visible = False

    def load(self):
        """Load the graphical components of the group."""
        self.loaded = True

    def show(self):
        """Show the widget in its parent."""
        self.frame.grid()
        self.visible = True

    def hide(self):
        """Hide the widget in its parent."""
        self.frame.grid_forget()
        self.visible = False


class HeaderView(GroupView):
    """The header group of the crossword application."""

    def __init__(self, root, parent):
        """Build the header widget group."""
        super().__init__(root, parent)
        # Crossword title
        self.title = tk.StringVar(self.root)
        self.title_label = tk.Label(self.frame, textvariable=self.title)
        # Crossword author
        self.author = tk.StringVar(self.root)
        self.author_label = tk.Label(self.frame, textvariable=self.author)
        # Dividing line separating the header and other groups
        self.separator = tk.Frame(self.frame)
        # Load
        self.load()

    def load(self):
        """Load the graphical components of the group."""
        # Frame
        self.frame.columnconfigure(0, weight=1)
        # Crossword title
        self.title_label.config(**settings.get("style:title"))
        self.title_label.grid(row=0, column=0, pady=(0, PAD), sticky=tk.W)
        # Crossword author
        self.author_label.config(**settings.get("style:author"))
        self.author_label.grid(row=0, column=0, padx=TINY_PAD, pady=(0, PAD), sticky=tk.E)
        # Separator
        self.separator.config(height=SEPARATOR_HEIGHT, bg=SEPARATOR_COLOR)
        self.separator.grid(row=1, padx=TINY_PAD, sticky=tk.W+tk.E)
        # Loaded
        self.loaded = True

    def show(self):
        """Show the widget in its parent."""
        # Custom grid the frame to the parent
        self.frame.grid(row=0, column=0, columnspan=4, padx=PAD, pady=(TINY_PAD, PAD), sticky=tk.W+tk.E)
        # Visibility
        self.visible = True


class PuzzleView(GroupView):
    """The puzzle group of the crossword application."""

    def __init__(self, root, parent):
        """Build the crossword widget group."""
        super().__init__(root, parent)
        # Crossword clue
        self.clue = tk.StringVar(self.root)
        self.clue_label = tk.Label(self.frame, textvariable=self.clue)
        # Game timer
        self.time = tk.StringVar(self.root)
        self.time_label = tk.Label(self.frame, textvariable=self.time)
        # Game canvas
        self.canvas = tk.Canvas(self.frame)
        # Load
        self.load()

    def load(self, width=DEFAULT_PUZZLE_WIDTH, height=DEFAULT_PUZZLE_HEIGHT):
        """Load the graphical components of the group."""
        self.frame.grid_configure(row=1, column=0, padx=PAD, pady=0)
        # Crossword clue
        self.clue_label.config(**settings.get("style:clue"))
        self.clue_label.grid(row=0, sticky=tk.W)
        # Game timer
        self.time_label.config(**settings.get("style:time"))
        self.time_label.grid(row=0, padx=TINY_PAD+1, sticky=tk.E)
        # Game canvas
        canvas_width = settings.get("board:cell-size")*width + CANVAS_SPARE
        canvas_height = settings.get("board:cell-size")*height + CANVAS_SPARE
        border_fill = settings.get("style:border:fill")
        self.canvas.config(width=canvas_width, height=canvas_height, highlightthickness=0)
        self.canvas.grid(row=1, pady=PAD, padx=(PAD-CANVAS_PAD, 0))
        self.canvas.create_rectangle(0, 0, canvas_width-CANVAS_SPARE, canvas_height-CANVAS_SPARE, outline=border_fill)
        # Loaded
        self.loaded = True


class CluesView(GroupView):
    """The clues group of the crossword application."""

    def __init__(self, root, parent):
        """Build the clues widget group."""
        super().__init__(root, parent)
        # Across label
        self.across_label = tk.Label(self.frame)
        # Across frame
        self.across = tk.Frame(self.frame)
        # Across list and scrollbar
        self.across_clues = tk.StringVar(self.root)
        self.across_listbox = tk.Listbox(self.across, listvariable=self.across_clues)
        self.across_scrollbar = tk.Scrollbar(self.across)
        # Down Label
        self.down_label = tk.Label(self.frame)
        # Down frame
        self.down = tk.Frame(self.frame)
        # Down list and scrollbar
        self.down_clues = tk.StringVar(self.root)
        self.down_listbox = tk.Listbox(self.down)
        self.down_scrollbar = tk.Scrollbar(self.down)
        # Load
        self.load()

    def load(self):
        """Load the graphical components of the group."""
        # Frame
        self.frame.grid_configure(row=1, column=1, padx=(PAD, PAD+TINY_PAD), pady=(0, PAD+CANVAS_PAD), sticky=tk.N+tk.S)
        self.frame.rowconfigure(1, weight=1)
        self.frame.rowconfigure(3, weight=1)
        # Across label
        self.across_label.config(text="Across", anchor=tk.W, **settings.get("style:clue"))
        self.across_label.grid(row=0, column=0, pady=(0, TINY_PAD), sticky=tk.N+tk.W)
        # Across frame
        self.across.config(highlightthickness=1, highlightbackground=settings.get("style:border:fill"))
        self.across.grid(row=1, pady=(CANVAS_PAD, PAD), sticky=tk.N+tk.S)
        self.across.rowconfigure(0, weight=1)
        # Across listbox
        self.across_listbox.config(bd=0, selectborderwidth=0, **settings.get("style:list"))
        self.across_listbox.grid(row=0, column=0, sticky=tk.N+tk.S)
        self.across_listbox.config(yscrollcommand=self.across_scrollbar.set)
        # Across scrollbar
        self.across_scrollbar.config(command=self.across_listbox.yview)
        self.across_scrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)
        # Down label
        self.down_label.config(text="Down", anchor=tk.W, **settings.get("style:clue"))
        self.down_label.grid(row=2, column=0, pady=(PAD, 0), sticky=tk.N+tk.W)
        # Down frame
        self.down.config(highlightthickness=1, highlightbackground=settings.get("style:border:fill"))
        self.down.grid(row=3, pady=(TINY_PAD, 0), sticky=tk.N+tk.S)
        self.down.rowconfigure(0, weight=1)
        # Down listbox
        self.down_listbox.config(bd=0, selectborderwidth=0, **settings.get("style:list"))
        self.down_listbox.grid(row=0, column=0, sticky=tk.N+tk.S)
        self.down_listbox.config(yscrollcommand=self.down_scrollbar.set)
        # Down scrollbar
        self.down_scrollbar.config(command=self.down_listbox.yview)
        self.down_scrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)
        # Loaded
        self.loaded = True
