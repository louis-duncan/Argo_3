import random
from .main import Game, Action


class GameObject:
    def __init__(self, parent, obj_id: int, pos=(0, 0), direction: int=0):
        """Base object for any game object."""
        self.parent: Game = parent
        self.id = obj_id
        self.pos: list = list(pos)
        self.direction: int = direction

        self.valid_actions = [
            "set_pos",
            "move",
            "forward", "fw",
            "backward", "bw",
            "turn",
            "left", "lt",
            "right", "rt",
            "destroy"
        ]

    def set_pos(self, pos):
        """Sets the absolute position of the object in the game space."""
        self.pos = list(pos)

    def move(self, dist=1):
        """Moves the object in the direction it is facing by the amount of 'dist'.
        Positive for forward, negative for backward."""
        if self.direction in (1, 2, 3):
            self.pos[0] += dist
        elif self.direction in (5, 6, 7):
            self.pos[0] -= dist

        if self.direction in (7, 0, 1):
            self.pos[1] += dist
        elif self.direction in (3, 4, 5):
            self.pos[1] -= dist

    def forward(self):
        """Shortcut for move(1)."""
        self.move(1)

    def backward(self):
        """Shortcut for move(-1)."""
        self.move(-1)

    def fw(self):
        """Shortcut for forward()."""
        self.forward()

    def bw(self):
        """Shortcut for backward()."""
        self.backward()

    def turn(self, dist=1):
        """Turns the object by the amount in 'dist'.
        Positive for right/clockwise, negative for left/anti-clockwise"""
        self.direction = (self.direction + dist) % 8

    def left(self):
        """Shortcut for turn(-1)."""
        self.turn(-1)

    def right(self):
        """Shortcut for turn(1)."""
        self.turn(1)

    def lt(self):
        """Shortcut for left()."""
        self.left()

    def rt(self):
        """Shortcut for right()."""
        self.right()

    def destroy(self):
        self.parent.destroy_object(self)

    def handle_action(self, action: Action):
        pass