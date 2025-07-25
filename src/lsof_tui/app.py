from abc import ABC, abstractmethod
from typing import Any, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.events import Resize
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Footer, Input, Collapsible
from textual.widgets.collapsible import CollapsibleTitle

from .model import NetworkModel, NetworkIOModel, ConnectionAttributes
from .widgets import IconLabelMetricWidget, IconMetricWidget, NetworkDataTable
from .constants import (
    BASIC_KEYBINDINGS,
    REFRESH_INTERVAL,
    DEFAULT_TITLE,
    ALL_INTERFACE,
    DEFAULT_SHOW_ICONS,
    ARCTIC_THEME,
    TYPE_ORDER,
    DEFAULT_COL_SORT,
    render_icon,
)

HELP_PANEL_MIN_WIDTH = 30
HELP_PANEL_MAX_WIDTH = 60
HELP_PANEL_WIDTH_PERCENT = 0.33


class PanelState(ABC):
    """
    Abstract base class for help panel states.
    """

    @staticmethod
    @abstractmethod
    def toggle(app: App):
        """
        Toggle the help panel state.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_renderable_width(screen_width: int) -> int:
        """
        Get the renderable width based on the screen width.
        """
        pass


class HelpPanelOpened(PanelState):
    """
    Represents the opened state of the help panel.
    """

    @staticmethod
    def toggle(app: App) -> "HelpPanelClosed":
        """
        Toggle the help panel to close.

        Args:
            app (App): The application instance.

        Returns:
            HelpPanelClosed: The new state of the help panel.
        """
        app.action_hide_help_panel()
        return HelpPanelClosed()

    @staticmethod
    def get_renderable_width(screen_width: int) -> int:
        """
        Compute the renderable width based on the screen width and the width of the help panel.

        Args:
            screen_width (int): The width of the screen.

        Returns:
            int: The renderable width.
        """
        return screen_width - max(
            min(int(screen_width * HELP_PANEL_WIDTH_PERCENT), HELP_PANEL_MAX_WIDTH),
            HELP_PANEL_MIN_WIDTH,
        )


class HelpPanelClosed(PanelState):
    """
    Represents the closed state of the help panel.
    """

    @staticmethod
    def toggle(app: App) -> HelpPanelOpened:
        """
        Toggle the help panel to open.

        Args:
            app (App): The application instance.

        Returns:
            HelpPanelOpened: The new state of the help panel.
        """
        app.action_show_help_panel()
        return HelpPanelOpened()

    @staticmethod
    def get_renderable_width(screen_width: int) -> int:
        """
        Compute the renderable width when the help panel is closed.

        Args:
            screen_width (int): The width of the screen.

        Returns:
            int: The renderable width.
        """
        return screen_width


class LsofApp(App):
    """
    The main application class for the TUI Lsof tool, which displays network connections
    and their metrics in a terminal user interface.
    """

    CSS_PATH = "assets/styles.tcss"
    TITLE = DEFAULT_TITLE
    BINDINGS = BASIC_KEYBINDINGS

    r_current_filter: reactive[str] = reactive("")
    r_sort_mode: reactive[str] = reactive(DEFAULT_COL_SORT)
    r_show_icons: reactive[bool] = reactive(DEFAULT_SHOW_ICONS)
    r_renderable_width: reactive[int] = reactive(0)

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the LsofApp with default settings and initialize the network model.
        """
        super().__init__(**kwargs)
        self.network: NetworkModel = NetworkModel()
        self._help_panel_st: PanelState = HelpPanelClosed()
        self.bandwidth: NetworkIOModel = NetworkIOModel()
        self.interface: reactive[str] = ALL_INTERFACE
        self._screen_width: int = 0
        self.register_theme(ARCTIC_THEME)
        self.theme = ARCTIC_THEME.name
        self.timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        with Vertical(id="app_vertical"):
            with Container(id="metrics_container"):
                with Horizontal():
                    with Horizontal(classes="col-8"):
                        yield IconLabelMetricWidget(
                            "nb_connections",
                            id="metric_nb_connections",
                            classes="metrics col-4",
                        ).data_bind(
                            r_show_icons=LsofApp.r_show_icons,
                            r_renderable_width=LsofApp.r_renderable_width,
                        )
                        yield IconLabelMetricWidget(
                            "nb_actives",
                            id="metric_nb_actives",
                            classes="metrics col-4",
                        ).data_bind(
                            r_show_icons=LsofApp.r_show_icons,
                            r_renderable_width=LsofApp.r_renderable_width,
                        )
                        yield IconLabelMetricWidget(
                            "nb_listening",
                            id="metric_nb_listening",
                            classes="metrics col-4",
                        ).data_bind(
                            r_show_icons=LsofApp.r_show_icons,
                            r_renderable_width=LsofApp.r_renderable_width,
                        )
                    yield IconMetricWidget(
                        "bandwidth_in",
                        id="metric_bandwidth_in",
                        classes="metrics col-2",
                    ).data_bind(
                        r_show_icons=LsofApp.r_show_icons,
                        r_renderable_width=LsofApp.r_renderable_width,
                    )
                    yield IconMetricWidget(
                        "bandwidth_out",
                        id="metric_bandwidth_out",
                        classes="metrics col-2",
                    ).data_bind(
                        r_show_icons=LsofApp.r_show_icons,
                        r_renderable_width=LsofApp.r_renderable_width,
                    )
            with Horizontal(id="table_container"):
                yield NetworkDataTable(self.network, id="table_connections").data_bind(
                    r_show_icons=LsofApp.r_show_icons,
                    r_renderable_width=LsofApp.r_renderable_width,
                )
            with Collapsible(
                id="filter_collapsible",
                title=f" {render_icon("filter", self.r_show_icons)}",
                collapsed=False,
                expanded_symbol="▼",
                collapsed_symbol="▲",
            ):
                yield Input(id="filter_input")
        yield Footer()

    def on_mount(self) -> None:
        """
        Focus the data table and initialize the timer for refreshing data.
        """
        self.log.debug(self.tree)
        self.timer: Timer = self.set_interval(REFRESH_INTERVAL, self._refresh_datatable)
        self.query_one(NetworkDataTable).focus()

    def _refresh_datatable(self) -> None:
        """
        Refresh the datatable by updating the network data and bandwidth metrics.
        """
        self.timer.pause()
        self.network.update_data()
        self.bandwidth.update_data(self.interface)
        self._update_metrics_display()
        self.query_one(NetworkDataTable).update_display()
        self.timer.resume()

    def _update_metrics_display(self) -> None:
        """
        Update the display of network metrics in the TUI.
        """
        self.query_one("#metric_nb_connections").r_value = (
            self.network.metrics.nb_connections
        )
        self.query_one("#metric_nb_actives").r_value = self.network.metrics.nb_actives
        self.query_one("#metric_nb_listening").r_value = (
            self.network.metrics.nb_listening
        )
        self.query_one("#metric_bandwidth_in").r_value = (
            self.bandwidth.render_bandwidth_in
        )
        self.query_one("#metric_bandwidth_out").r_value = (
            self.bandwidth.render_bandwidth_out
        )

    def _update_renderable_width(self):
        """
        Update the renderable width based on the current screen width and the help panel state.
        """
        self.r_renderable_width = self._help_panel_st.get_renderable_width(
            self._screen_width
        )

    def on_resize(self, event: Resize) -> None:
        """
        Handle the resize event to update the screen width and adjust the renderable width.
        """
        self._screen_width = event.size.width
        self._update_renderable_width()

    def on_input_changed(self, event: Input.Changed) -> None:
        """
        Handle input changes to filter the network connections.
        """
        if event.input.id == "filter_input":
            self.network.filter(event.value)
            self.query_one(NetworkDataTable).update_display()

    def action_sort_by_status(self) -> None:
        """
        Sort connections by their status.
        """
        self.network.reorder("status")
        self.query_one(NetworkDataTable).sort("status", key=lambda text: text.plain)

    def action_sort(self, col_key: ConnectionAttributes) -> None:
        """
        Sort the network connections by the specified attribute.

        Args:
            col_key (str): The attribute key
        """
        self.network.reorder(col_key)
        self.query_one(NetworkDataTable).sort(
            col_key, key=lambda v: TYPE_ORDER.get(col_key, str)(v)
        )

    def action_toggle_icons(self) -> None:
        """
        Toggle the visibility of icons in the data table.
        """
        self.r_show_icons = not self.r_show_icons

    def action_toggle_filter(self) -> None:
        """
        Toggle the visibility of the filter collapsible section.
        """
        self.query_one("#filter_collapsible", Collapsible).post_message(
            CollapsibleTitle.Toggle()
        )

    def action_toggle_shortcut(self) -> None:
        """
        Open/Close the help panel.
        """
        self._help_panel_st = self._help_panel_st.toggle(self)
        self._update_renderable_width()
