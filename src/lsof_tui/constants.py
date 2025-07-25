from textual.theme import Theme
from textual.binding import Binding
from rich.emoji import Emoji

DEFAULT_COL_SORT = "name"
DEFAULT_TITLE = "lsof TUI"
ALL_INTERFACE = "all"
DEFAULT_SHOW_ICONS = True
DEFAULT_COLUMNS = ["pid", "name", "protocol", "laddr", "raddr", "status", "ns"]
RESPONSIVE_COLUMNS = [False, False, False, True, True, False, True]
DATATABLE_MIN_WIDTH = [10, 15, 15, 20, 20, 12, 20]
REFRESH_COLUMNS = ["status"]

DEVICES_WIDTH = [120, 60, 0]
DEVICES_NAMES = ["lg", "md", "sm"]
DATATABLE_HEADER_HEIGHT = 3

ARCTIC_THEME = Theme(
    name="arctic",
    primary="#88C0D0",
    secondary="#81A1C1",
    accent="#B48EAD",
    foreground="#D8DEE9",
    background="#2E3440",
    success="#A3BE8C",
    warning="#EBCB8B",
    error="#BF616A",
    surface="#3B4252",
    panel="#434C5EFF",
    dark=True,
    variables={
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#88C0D0",
        "input-selection-background": "#81a1c1 35%",
    },
)
REFRESH_INTERVAL = 0.5  # seconds
BASIC_KEYBINDINGS = [
    Binding("q", "quit", "Quit"),
    Binding("f", "toggle_filter", "Filter connections (support regex)", show=False),
    Binding("s", "sort_by_status", "Sort by status", show=False),
    Binding("t", "sort('pid')", "Sort by pid", show=False),
    Binding("y", "sort('name')", "Sort by name", show=False),
    Binding("u", "sort('protocol')", "Sort by protocol", show=False),
    Binding("i", "sort('laddr')", "Sort by local address", show=False),
    Binding("o", "sort('raddr')", "Sort by remote address", show=False),
    Binding("p", "sort('ns')", "Sort by hostname", show=False),
    Binding("x", "toggle_shortcut", "Show/Hide Shortcut page"),
    Binding("e", "toggle_icons", "Show/Hide Icons"),
]

TYPE_ORDER = {"pid": int}

ICONS = {
    "LISTEN": ("up", "LISTEN"),
    "ESTABLISHED": ("left_right_arrow", "ESTABLISHED"),
    "CLOSE_WAIT": ("hourglass_flowing_sand", "CLOSE_WAIT"),
    "TIME_WAIT": ("chequered_flag", "TIME_WAIT"),
    "SYN_SENT": ("hourglass_flowing_sand", "SYN_SENT"),
    "SYN_RECV": ("hourglass_flowing_sand", "SYN_RECV"),
    "FIN_WAIT1": ("hourglass_flowing_sand", "FIN_WAIT1"),
    "FIN_WAIT2": ("hourglass_done", "FIN_WAIT2"),
    "CLOSING": ("hourglass_done", "CLOSING"),
    "LAST_ACK": ("chequered_flag", "LAST_ACK"),
    "nb_connections": ("globe_with_meridians", "Connections"),
    "nb_actives": ("left_right_arrow", "Actives"),
    "nb_listening": ("up", "Listening"),
    "bandwidth_in": ("inbox_tray", "D"),
    "bandwidth_out": ("outbox_tray", "U"),
    "pid": ("id", "PID"),
    "name": ("thread", "Process"),
    "laddr": ("laptop_computer", "Local Address"),
    "raddr": ("globe_with_meridians", "Remote Address"),
    "ns": ("link", "Hostname"),
    "status": ("lantern", "State"),
    "protocol": ("wrench", "Protocol"),
    "filter": ("mag", "Filter"),
}


def render_icon(icon: str, show_icon: bool = True) -> str:
    """
    Render an icon based on the provided icon name and whether to show it.

    Args:
        icon (str): The name of the icon to render.
        show_icon (bool): Whether to show the icon or not.

    Returns:
        str: The rendered icon as a string, or an empty string if the icon parameter is an empty string or show_icon is False.
    """
    if icon == "" or not show_icon:
        return ""
    return str(Emoji(ICONS.get(icon)[0], variant="emoji"))


def render_icon_label(icon: str) -> str:
    """
    Render the label for an icon based on the provided icon name.

    Args:
        icon (str): The name of the icon to render the label for.

    Returns:
        str: The label for the icon, or an empty string if the icon parameter is an empty string.
    """
    if icon == "":
        return ""
    return ICONS.get(icon)[1]


def render_icon_or_label(icon: str, show_icon: bool):
    """
    Render either an icon or its label based on the show_icon parameter.

    Args:
        icon (str): The name of the icon to render.
        show_icon (bool): Whether to show the icon or the label.

    Returns:
        str: The rendered icon or label, or an empty string if the icon parameter is an empty string.
    """
    if icon == "":
        return ""
    return render_icon(icon, show_icon) if show_icon else render_icon_label(icon)
