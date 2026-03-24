# Battleship Game
import os
import re
import sys
import random
from colorama import init, Fore, Style
from wcwidth import wcswidth

if os.name == "nt":
    import msvcrt
else:
    import tty
    import termios

# Initialize colorama (cross-platform color support)
init(autoreset=True)


# ========= 1) Welcome Screen =========
class WelcomeScreen:
    """Arcade-style welcome screen with inline setup boxes."""

    def __init__(self, title_lines, ship_art, width=100):
        self.title_lines = title_lines
        self.ship_art = ship_art
        self.width = max(width, 118)

    # ----- Utility Functions -----
    def strip_ansi(self, text: str) -> str:
        """Remove ANSI escape codes for alignment math."""
        ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        return ansi_escape.sub("", text)

    def visible_width(self, text: str) -> int:
        """Return visible width of text, ignoring ANSI color codes."""
        clean_text = self.strip_ansi(text)
        width = wcswidth(clean_text)
        return len(clean_text) if width < 0 else width

    def center_text(self, text: str, color: str = "") -> str:
        """Return centered text with optional color."""
        clean_width = self.visible_width(text)
        pad = max(0, (self.width - clean_width) // 2)
        return " " * pad + color + text + Style.RESET_ALL

    def pad_line(
        self,
        text: str,
        target_width: int,
        align: str = "left",
    ) -> str:
        """Pad one line to target width."""
        current = self.visible_width(text)

        if current >= target_width:
            return text

        if align == "center":
            left = (target_width - current) // 2
            right = target_width - current - left
            return (" " * left) + text + (" " * right)

        return text + (" " * (target_width - current))

    def gradient_line(self, text: str) -> str:
        """Apply rainbow gradient across one line of the title."""
        colors = [
            Fore.RED,
            Fore.MAGENTA,
            Fore.BLUE,
            Fore.CYAN,
            Fore.GREEN,
            Fore.YELLOW,
        ]
        n = len(text)
        gradient = ""
        for i, ch in enumerate(text):
            color = colors[int((i / max(1, n - 1)) * (len(colors) - 1))]
            gradient += color + ch
        return gradient + Style.RESET_ALL

    def build_panel_lines(
        self,
        title: str,
        lines: list[str],
        panel_width: int,
        align: str = "left",
        border_color: str = Fore.YELLOW,
        title_color: str = Fore.CYAN,
    ) -> list[str]:
        """Build one panel using board-style borders."""
        inner_width = panel_width - 2
        label = f" {title} "
        label_width = self.visible_width(label)
        spare = max(0, inner_width - label_width)
        left = spare // 2
        right = spare - left

        top = (
            border_color
            + "┌"
            + ("─" * left)
            + title_color
            + label
            + border_color
            + ("─" * right)
            + "┐"
            + Style.RESET_ALL
        )
        bottom = (
            border_color
            + "└"
            + ("─" * inner_width)
            + "┘"
            + Style.RESET_ALL
        )

        panel = [top]

        for line in lines:
            padded = self.pad_line(line, inner_width, align=align)
            row = (
                border_color
                + "│"
                + Style.RESET_ALL
                + padded
                + border_color
                + "│"
                + Style.RESET_ALL
            )
            panel.append(row)

        panel.append(bottom)
        return panel

    def print_panel(self, title: str, lines: list[str], align: str = "left"):
        """Print a centered full-width panel."""
        panel_lines = self.build_panel_lines(
            title,
            lines,
            self.width,
            align=align,
        )
        for line in panel_lines:
            print(self.center_text(line))

    def print_side_by_side_panels(
        self,
        left_title: str,
        left_lines: list[str],
        right_title: str,
        right_lines: list[str],
    ):
        """Print two panels side by side."""
        gap = " " * 4
        panel_width = (self.width - 4) // 2

        left_panel = self.build_panel_lines(
            left_title,
            left_lines,
            panel_width,
            align="center",
        )
        right_panel = self.build_panel_lines(
            right_title,
            right_lines,
            panel_width,
            align="left",
        )

        max_lines = max(len(left_panel), len(right_panel))

        while len(left_panel) < max_lines:
            left_panel.insert(-1, "│" + (" " * (panel_width - 2)) + "│")
        while len(right_panel) < max_lines:
            right_panel.insert(-1, "│" + (" " * (panel_width - 2)) + "│")

        for left_row, right_row in zip(left_panel, right_panel):
            print(self.center_text(left_row + gap + right_row))

    def selector_row(
        self,
        label: str,
        min_value: int,
        max_value: int,
        value_text: str,
        selected: bool = False,
    ) -> str:
        """Render one setup row aligned for the inner mission panel."""
        display_value = value_text if value_text else ""
        display_value = display_value[:3]

        label_part = f"{label} ({min_value}-{max_value})".ljust(24)
        value_box = f"[  {display_value:^3}  ]"
        marker = "> " if selected else "  "
        row = marker + label_part + "     " + value_box

        if selected:
            return (
                Style.BRIGHT
                + Fore.CYAN
                + marker
                + label_part
                + Fore.YELLOW
                + "     "
                + value_box
                + Style.RESET_ALL
            )

        return (
            Fore.WHITE + row + Style.RESET_ALL
        )

    def action_row(self, label: str, selected: bool = False) -> str:
        """Render the deploy button for the inner mission panel."""
        button = "[ DEPLOY FLEET ]"

        if selected:
            return (
                Style.BRIGHT
                + Fore.GREEN
                + "[ PRESS ENTER TO START ]"
                + Style.RESET_ALL
            )
        return Fore.WHITE + button + Style.RESET_ALL

    def read_key(self) -> str:
        """Read one key without showing an extra input prompt."""
        if os.name == "nt":
            key = msvcrt.getwch()

            if key in ("\x00", "\xe0"):
                special = msvcrt.getwch()
                mapping = {
                    "H": "up",
                    "P": "down",
                    "K": "left",
                    "M": "right",
                }
                return mapping.get(special, "")

            if key == "\r":
                return "enter"

            if key == "\x08":
                return "backspace"

            return key.lower()

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)

            if key == "\x1b":
                next1 = sys.stdin.read(1)
                next2 = sys.stdin.read(1)
                if next1 == "[":
                    mapping = {
                        "A": "up",
                        "B": "down",
                        "D": "left",
                        "C": "right",
                    }
                    return mapping.get(next2, "")
                return ""

            if key in ("\r", "\n"):
                return "enter"

            if key in ("\x7f", "\b"):
                return "backspace"

            return key.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    # ----- Title -----
    def show_title(self):
        """Show original colorful title and top console strip."""
        clear_screen()
        print("\n")

        for line in self.title_lines:
            print(self.center_text(self.gradient_line(line)))

        print("\n")

        tagline = "⚓  Command Center Online - Prepare for Battle  ⚓"
        line = Fore.YELLOW + "═" * self.width + Style.RESET_ALL
        print(self.center_text(line))
        print(self.center_text(tagline, color=Style.BRIGHT + Fore.CYAN))
        print(self.center_text(line))
        print()

    # ----- Ship Art -----
    def show_ship(self):
        """Show original ship art inside a bigger box."""
        art_lines = ["", ""]
        for line in self.ship_art.splitlines():
            if line.strip():
                art_lines.append(Fore.GREEN + line + Style.RESET_ALL)
        art_lines.extend(["", ""])

        self.print_panel("FLEET VISUAL", art_lines, align="center")
        print()

    # ----- Input Screen -----
    def render_setup_screen(
        self,
        grid_text: str,
        ships_text: str,
        selected: int,
        message: str = "",
    ):
        """Render mission setup with centered content and no inner frame."""
        self.show_title()
        self.show_ship()

        setup_lines = [
            "",
            self.pad_line(
                (
                    Fore.WHITE
                    + "Choose your battlefield settings before deployment."
                    + Style.RESET_ALL
                ),
                self.width - 2,
                align="center",
            ),
            "",
            self.pad_line(
                self.selector_row(
                    "GRID SIZE",
                    8,
                    15,
                    grid_text,
                    selected == 0,
                ),
                self.width - 2,
                align="center",
            ),
            "",
            self.pad_line(
                self.selector_row(
                    "NUMBER OF SHIPS",
                    1,
                    5,
                    ships_text,
                    selected == 1,
                ),
                self.width - 2,
                align="center",
            ),
            "",
            self.pad_line(
                self.action_row("DEPLOY FLEET", selected == 2),
                self.width - 2,
                align="center",
            ),
            "",
            self.pad_line(
                Fore.GREEN + "Use ↑/↓ to select an option." + Style.RESET_ALL,
                self.width - 2,
                align="center",
            ),
            self.pad_line(
                (
                    Fore.GREEN
                    + "Use ←/→ or number keys to change the selected value."
                    + Style.RESET_ALL
                ),
                self.width - 2,
                align="center",
            ),
            self.pad_line(
                (
                    Fore.GREEN
                    + "Press Enter to confirm the selected option."
                    + Style.RESET_ALL
                ),
                self.width - 2,
                align="center",
            ),
            "",
        ]

        self.print_panel("MISSION SETUP", setup_lines, align="left")

        if message:
            print()
            print(
                self.center_text(
                    Fore.RED + Style.BRIGHT + message + Style.RESET_ALL
                )
            )

        print()

    def get_inputs(self):
        """Inline box editing inside mission setup."""
        grid_text = "8"
        ships_text = "3"
        selected = 0
        message = ""

        while True:
            self.render_setup_screen(
                grid_text,
                ships_text,
                selected,
                message,
            )
            key = self.read_key()
            message = ""

            if key == "up":
                selected = max(0, selected - 1)
                continue

            if key == "down":
                selected = min(2, selected + 1)
                continue

            if key == "backspace":
                if selected == 0:
                    grid_text = grid_text[:-1]
                elif selected == 1:
                    ships_text = ships_text[:-1]
                continue

            if key == "left":
                if selected == 0:
                    current = int(grid_text) if grid_text.isdigit() else 8
                    current = 15 if current <= 8 else current - 1
                    grid_text = str(current)
                elif selected == 1:
                    current = int(ships_text) if ships_text.isdigit() else 3
                    current = 5 if current <= 1 else current - 1
                    ships_text = str(current)
                continue

            if key == "right":
                if selected == 0:
                    current = int(grid_text) if grid_text.isdigit() else 8
                    current = 8 if current >= 15 else current + 1
                    grid_text = str(current)
                elif selected == 1:
                    current = int(ships_text) if ships_text.isdigit() else 3
                    current = 1 if current >= 5 else current + 1
                    ships_text = str(current)
                continue

            if key == "enter":
                if selected == 0:
                    if grid_text.isdigit() and 8 <= int(grid_text) <= 15:
                        selected = 1
                    else:
                        message = "GRID SIZE must be between 8 and 15."
                    continue

                if selected == 1:
                    if ships_text.isdigit() and 1 <= int(ships_text) <= 5:
                        selected = 2
                    else:
                        message = "NUMBER OF SHIPS must be between 1 and 5."
                    continue

                if selected == 2:
                    if not (grid_text.isdigit() and 8 <= int(grid_text) <= 15):
                        message = "GRID SIZE must be between 8 and 15."
                        selected = 0
                        continue

                    if not (
                        ships_text.isdigit()
                        and 1 <= int(ships_text) <= 5
                    ):
                        message = "NUMBER OF SHIPS must be between 1 and 5."
                        selected = 1
                        continue

                    return int(grid_text), int(ships_text)

            if len(key) == 1 and key.isdigit():
                if selected == 0:
                    if grid_text in ("8", ""):
                        grid_text = key
                    elif len(grid_text) < 2:
                        grid_text += key
                    else:
                        grid_text = key

                elif selected == 1:
                    if ships_text in ("3", ""):
                        ships_text = key
                    else:
                        ships_text = key
                continue

    # ----- Mission Briefing -----
    def mission_briefing(self, size, ships):
        """Show briefing and tactical console in boxed arcade layout."""
        max_row = chr(64 + size)

        left_lines = [
            (
                Fore.YELLOW
                + Style.BRIGHT
                + "INCOMING TRANSMISSION"
                + Style.RESET_ALL
            ),
            "",
            Fore.CYAN + "Welcome, Commander." + Style.RESET_ALL,
            "Enemy fleets lurk beyond the horizon...",
            f"Tactical grid: {size}x{size} sectors (A-{max_row}, 1-{size})",
            f"Fleet deployed: {ships} battleships",
            "Enemy ships are hidden.",
            "Hunt them down with precision fire!",
        ]

        right_lines = [
            (
                Fore.MAGENTA
                + Style.BRIGHT
                + "TACTICAL ORDERS"
                + Style.RESET_ALL
            ),
            "",
            "- Enter strike coordinates like A1, C7, or H8",
            f"- {HIT}  Direct hit on enemy ship",
            f"- {MISS}  Splash! Shot missed",
            f"- {WATER}  Untouched waters",
            f"- {SHIP_CHAR}  Your ship positions (your radar only)",
            "",
            (
                Fore.YELLOW
                + Style.BRIGHT
                + "RULES OF ENGAGEMENT"
                + Style.RESET_ALL
            ),
            "- Turns alternate - one strike per side.",
            "- Victory: Destroy the enemy fleet.",
            "- Defeat: All your ships are sunk.",
        ]

        clear_screen()
        self.show_title()
        self.show_ship()

        self.print_side_by_side_panels(
            "MISSION BRIEFING",
            left_lines,
            "TACTICAL CONSOLE",
            right_lines,
        )

        print()

        deploy_lines = [
            (
                "Stay sharp, Commander. The fate of the fleet "
                "rests in your hands."
            ),
            "",
            (
                Fore.GREEN
                + Style.BRIGHT
                + "Press Enter to deploy your fleet..."
                + Style.RESET_ALL
            ),
        ]
        self.print_panel("DEPLOYMENT", deploy_lines, align="center")

        input()
        clear_screen()


# ========= 2) Battleship Game =========
# Emoji constants
WATER = "🌊"
MISS = "💦"
HIT = "💥"
SHIP_CHAR = "🚢"

LEFT_TITLE = "Enemy Fleet"
RIGHT_TITLE = "Your Fleet"
CELL_VISUAL = 3
GAP_BETWEEN_BOARDS = " " * 8


def clear_screen():
    """Clear terminal window (Windows & Unix)."""
    os.system("cls" if os.name == "nt" else "clear")


def strip_ansi(s: str) -> str:
    """Strip ANSI color codes (fixes alignment math)."""
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def pad_visual(s: str, width: int) -> str:
    """Pad text so visual width matches width (handles emoji)."""
    vis = wcswidth(strip_ansi(s))
    if vis < 0:
        vis = len(strip_ansi(s))
    return s + " " * max(0, width - vis)


def format_cell(symbol: str) -> str:
    """Return one cell padded to CELL_VISUAL columns."""
    return pad_visual(symbol, CELL_VISUAL)


def build_board_block(
    title_text: str,
    grid_rows: list[list[str]],
) -> list[str]:
    """Build one framed board with title, numbers, rows, and border."""
    size = len(grid_rows)
    inner_width = 3 + (size * CELL_VISUAL)
    lines = []

    label = f" {title_text} "
    spare = inner_width - len(strip_ansi(label))
    left = max(0, spare // 2)
    right = max(0, spare - left)
    lines.append("┌" + ("─" * left) + label + ("─" * right) + "┐")

    nums = "".join(format_cell(str(i)) for i in range(1, size + 1))
    lines.append("│" + "   " + nums + "│")

    for r in range(size):
        row_label = chr(65 + r)
        row_cells = "".join(format_cell(ch) for ch in grid_rows[r])
        content = f"{row_label}  {row_cells}"
        content = pad_visual(content, inner_width)
        lines.append("│" + content + "│")

    lines.append("└" + ("─" * inner_width) + "┘")
    return lines


def display_boards(enemy_view: list[list[str]], player_board: list[list[str]]):
    """Print enemy + player boards side-by-side."""
    left_block = build_board_block(LEFT_TITLE, enemy_view)
    right_block = build_board_block(RIGHT_TITLE, player_board)
    for left_row, right_row in zip(left_block, right_block):
        print(left_row + GAP_BETWEEN_BOARDS + right_row)


class BattleshipGame:
    """Main Battleship game logic."""

    def __init__(self, size=8, num_ships=3, title_lines=None):
        self.size = size
        self.num_ships = num_ships
        self.enemy_view = [[WATER] * size for _ in range(size)]
        self.player_board = [[WATER] * size for _ in range(size)]
        self.enemy_ships = self._place_ships()
        self.player_ships = self._place_ships(reveal=True)
        self.enemy_tried = set()
        self.total_player_shots = 0
        self.total_enemy_shots = 0
        self.player_msg = ""
        self.enemy_msg = ""
        self.title_lines = title_lines or []

    def _place_ships(self, reveal=False):
        """Randomly place ships."""
        ships = set()
        while len(ships) < self.num_ships:
            r = random.randint(0, self.size - 1)
            c = random.randint(0, self.size - 1)
            ships.add((r, c))
        if reveal:
            for r, c in ships:
                self.player_board[r][c] = SHIP_CHAR
        return ships

    def _print_ascii_banner(self):
        """Print title above the boards."""
        board_width = 3 + (self.size * CELL_VISUAL)
        total_width = (board_width * 2) + len(GAP_BETWEEN_BOARDS)
        for line in self.title_lines:
            print(line.center(total_width))
        print()

    def play(self):
        """Main loop."""
        while self.player_ships and self.enemy_ships:
            clear_screen()

            self._print_ascii_banner()
            display_boards(self.enemy_view, self.player_board)
            self._show_status(current_turn="Player")

            self._player_turn()
            if not self.enemy_ships:
                break

            self.enemy_msg = self._enemy_turn()

            clear_screen()

            self._print_ascii_banner()
            display_boards(self.enemy_view, self.player_board)
            self._show_status(current_turn="Enemy")

        self._end_screen()

    def _player_turn(self):
        """Ask player for input and resolve strike."""
        guess = input(
            Fore.YELLOW + "\nEnter position (e.g., A1) or Q to quit: "
            + Style.RESET_ALL
        ).strip().upper()

        if guess == "Q":
            clear_screen()
            print("👋 Game ended by user.")
            raise SystemExit

        if len(guess) < 2:
            self.player_msg = "❌ Format must be Letter+Number (e.g., A1)."
            return

        row_letter, digits = guess[0], guess[1:]
        if not digits.isdigit():
            self.player_msg = "❌ Column must be a number (e.g., A1)."
            return

        r = ord(row_letter) - 65
        c = int(digits) - 1
        if not (0 <= r < self.size and 0 <= c < self.size):
            self.player_msg = (
                f"❌ Coordinates must be "
                f"A-{chr(64 + self.size)} + 1-{self.size}."
            )
            return

        if self.enemy_view[r][c] in (MISS, HIT):
            self.player_msg = "⚠️ Already tried that sector."
            return

        self.total_player_shots += 1
        if (r, c) in self.enemy_ships:
            self.enemy_view[r][c] = HIT
            self.enemy_ships.remove((r, c))
            self.player_msg = (
                f"💥 Direct Hit! Enemy ship damaged at "
                f"{row_letter}{c + 1}!"
            )
        else:
            self.enemy_view[r][c] = MISS
            self.player_msg = (
                f"💦 Torpedo missed at {row_letter}{c + 1}, "
                "enemy evaded!"
            )

    def _enemy_turn(self):
        """Enemy AI randomly fires at player fleet."""
        while True:
            r = random.randint(0, self.size - 1)
            c = random.randint(0, self.size - 1)
            if (r, c) not in self.enemy_tried:
                self.enemy_tried.add((r, c))
                break

        self.total_enemy_shots += 1
        pos = f"{chr(65 + r)}{c + 1}"

        if (r, c) in self.player_ships:
            self.player_board[r][c] = HIT
            self.player_ships.remove((r, c))
            return f"💥 Enemy fires at {pos} - Direct Hit!"

        self.player_board[r][c] = MISS
        return f"💦 Enemy fires at {pos} - Torpedo missed, you evaded!"

    def _show_status(self, current_turn="Player"):
        """Show compact status info."""
        enemy_left = len(self.enemy_ships)
        player_left = len(self.player_ships)

        player_bar = (
            " ".join([SHIP_CHAR] * player_left) if player_left else "-"
        )
        enemy_bar = " ".join([SHIP_CHAR] * enemy_left) if enemy_left else "-"

        if current_turn == "Player":
            turn_text = Fore.CYAN + "🎯 Turn: Player" + Style.RESET_ALL
        else:
            turn_text = Fore.MAGENTA + "👾 Turn: Enemy" + Style.RESET_ALL

        print(
            f"{turn_text} | "
            f"Enemy ships: {enemy_left} {enemy_bar} | "
            f"Your ships: {player_left} {player_bar}"
        )
        print(
            f"Shots - Player: {self.total_player_shots} | "
            f"Enemy: {self.total_enemy_shots}"
        )
        print()

        if self.player_msg:
            print(Fore.CYAN + self.player_msg + Style.RESET_ALL)
        if self.enemy_msg:
            print(Fore.MAGENTA + self.enemy_msg + Style.RESET_ALL)

        legend = (
            f"{HIT}=Hit   {MISS}=Miss   "
            f"{WATER}=Water   {SHIP_CHAR}=Player"
        )
        print("\n" + Fore.YELLOW + "Legend: " + Style.RESET_ALL + legend)

    def _end_screen(self):
        """Final victory or defeat screen."""
        clear_screen()
        if self.enemy_ships and not self.player_ships:
            print("💀 Game Over: All your ships sunk.")
        elif self.player_ships and not self.enemy_ships:
            print("🏆 Victory: All enemy ships sunk! 🎉")


# ========= 3) Run Game =========
if __name__ == "__main__":
    title_lines = [
        ("██████   █████  ████████ ████████ ██      ███████ ███████ "
         "██   ██ ██ ██████  ███████"),
        ("██   ██ ██   ██    ██       ██    ██      ██      ██      "
         "██   ██ ██ ██   ██ ██     "),
        ("██████  ███████    ██       ██    ██      █████   ███████ "
         "███████ ██ ██████  ███████"),
        ("██   ██ ██   ██    ██       ██    ██      ██           ██ "
         "██   ██ ██ ██           ██"),
        ("██████  ██   ██    ██       ██    ███████ ███████ ███████ "
         "██   ██ ██ ██      ███████"),
    ]

    ship_art = r"""
⣠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠰⠶⢿⡶⠦⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢀⣀⣿⣿⣿⣿⣿⣿⡇⢀⠀⢀⡀⠀⣀⣀⣠⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠉⠻⠿⣿⣿⣿⣿⣿⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣶⣿⣿⣶⣶⣾⣧⣤⣴⣆⣀⢀⣤⡄⠀⠀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""

    ws = WelcomeScreen(title_lines, ship_art, width=100)
    ws.show_title()
    ws.show_ship()
    size, ships = ws.get_inputs()
    ws.mission_briefing(size, ships)

    game = BattleshipGame(size=size, num_ships=ships, title_lines=title_lines)
    game.play()
