"""The Snake entity: movement, growth, and AI planning."""
from .ai import bfs_direction, survival_direction


class Snake:
    """A single snake body with movement and self/obstacle awareness."""

    def __init__(self, body, direction, color, is_ai=False):
        self.body = list(body)          # head is body[0]
        self.direction = direction
        self.pending = direction
        self.color = color
        self.is_ai = is_ai
        self.alive = True
        self.grow_pending = 0
        self.score = 0
        self.cycle = None               # set for Hamiltonian fill AI

    @property
    def head(self):
        return self.body[0]

    def set_direction(self, direction):
        # Disallow reversing directly onto the neck.
        if (direction[0] == -self.direction[0]
                and direction[1] == -self.direction[1]):
            return
        self.pending = direction

    def plan_ai(self, food, blocked):
        """Choose a direction using BFS, falling back to survival."""
        direction = bfs_direction(self.head, food, blocked)
        if direction is None:
            direction = survival_direction(self.head, blocked, self.direction)
        if direction is not None:
            self.set_direction(direction)

    def plan_cycle(self):
        """Follow the Hamiltonian cycle (authoritative; bypasses the guard)."""
        hx, hy = self.head
        nx, ny = self.cycle[self.head]
        self.pending = (nx - hx, ny - hy)

    def step(self):
        self.direction = self.pending
        x, y = self.head
        new_head = (x + self.direction[0], y + self.direction[1])
        self.body.insert(0, new_head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

    def grow(self, amount=1):
        self.grow_pending += amount
