from typing import Any, override, Literal, Generator, Tuple, cast

from rich.align import Align
from rich.text import Text

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Static, Label
from textual.widgets.data_table import RowDoesNotExist, CellType, RowKey

from .constants import (
    DEFAULT_SHOW_ICONS,
    DEFAULT_COLUMNS,
    RESPONSIVE_COLUMNS,
    DATATABLE_MIN_WIDTH,
    REFRESH_COLUMNS,
    DEVICES_WIDTH,
    DEVICES_NAMES,
    DATATABLE_HEADER_HEIGHT,
    render_icon,
    render_icon_label,
    render_icon_or_label,
)
from .model import NetworkModel, ConnectionModel


class ResponsiveWidget(Static):
    """
    A widget that adjusts its layout based on the available width and the CSS classes.
    """

    r_renderable_width: reactive[bool] = reactive(0)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @staticmethod
    def get_pattern(new_width: int) -> str:
        """
        Get the CSS class pattern based on the new renderable width.

        Args:
            new_width (int): The new renderable width.

        Returns:
            str: The CSS class pattern to use for responsive design.
        """
        i = 0
        while i < len(DEVICES_WIDTH) and new_width < DEVICES_WIDTH[i]:
            i += 1
        return f"col-{DEVICES_NAMES[i]}-"

    @staticmethod
    def _match_css_classes(child: Widget, pattern: str) -> str | None:
        """
        Match the CSS classes of a child widget against a given pattern.

        Args:
            child (Widget): The child widget to check.
            pattern (str): The CSS class pattern to match against.

        Returns:
            str | None: The matched CSS class suffix if found, otherwise None.
        """
        for css_cls in child._classes:
            if css_cls.startswith(pattern):
                return css_cls[len(pattern) :]
        return None

    def _get_children_with_match(
        self, pattern: str
    ) -> Generator[Tuple[Widget, str | None]]:
        """
        Get all children widgets that have the .

        Args:
            pattern (str): The CSS class pattern to match against.

        Yields:
            Tuple[Widget, str | None]: A tuple containing the child widget and the matched CSS class suffix.
        """
        for child in self.query_children(".col"):
            yield child, self._match_css_classes(child, pattern)

    def watch_r_renderable_width(self, _: int, new_width: int) -> None:
        """
        Watch for changes in the renderable width and update the widths of the child widgets accordingly.
        """
        pattern = self.get_pattern(new_width)
        for child, w in self._get_children_with_match(pattern):
            if w is None:
                child.set_styles(f"display:none;")
            else:
                child.set_styles(f"display:block;")
                child.set_styles(f"width:{w}fr;")


class IconMetricWidget(ResponsiveWidget):
    """
    A widget to display a metric with an icon and a value.
    """

    r_value: reactive[str] = reactive("0")
    r_show_icons: reactive[bool] = reactive(DEFAULT_SHOW_ICONS)

    def __init__(self, icon: str, **kwargs: Any) -> None:
        """
        Initialize the IconMetricWidget with an icon and other parameters.

        Args:
            icon (str): The icon to display.
            **kwargs: Additional keyword arguments for the widget.
        """
        self._icon: str = icon
        super().__init__(**kwargs)

    @override
    def compose(self) -> ComposeResult:
        yield Label(classes="col col-lg-4 col-md-3 icons")
        yield Label(classes="col col-lg-8 col-md-9 col-sm-12 metric_value")

    def watch_r_show_icons(self, v: str) -> None:
        """
        Show/Hide the icon.
        """
        self.query_one(".icons").update(
            render_icon_or_label(self._icon, self.r_show_icons)
        )

    def watch_r_value(self, v: str) -> None:
        """
        Update the metric value displayed in the widget.
        """
        self.query_one(".metric_value").update(f"{self.r_value}")


class IconLabelMetricWidget(IconMetricWidget):
    """
    A widget to display a metric with an icon and a label, along with the value.
    """

    def __init__(self, *args, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @override
    def compose(self) -> ComposeResult:
        yield Label(classes="col col-lg-2 col-md-4 icons")
        yield Label(classes="col col-lg-6 metric_label")
        yield Label(classes="col col-lg-4 col-md-8 col-sm-12 metric_value")

    @override
    def watch_r_show_icons(self, v: str) -> None:
        """
        Show/Hide the icon.
        """
        self.query_one(".icons").update(render_icon(self._icon, self.r_show_icons))

    @override
    def watch_r_value(self, new_val: str) -> None:
        """
        Update the metric value and label displayed in the widget.

        Args:
            new_val (str): The new value to display.
        """
        super().watch_r_value(new_val)
        self.query_one(".metric_label").update(render_icon_label(self._icon))


class NetworkDataTable(DataTable):
    """
    A DataTable widget to display network connections with responsive columns and icons.
    """

    r_show_icons: reactive[bool] = reactive(DEFAULT_SHOW_ICONS)
    r_renderable_width: reactive[bool] = reactive(sum(DATATABLE_MIN_WIDTH))

    def __init__(self, network, *args, **kwargs) -> None:
        """
        Initialize the NetworkDataTable.

        Args:
            network (NetworkModel): The network model containing connection data.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self._network: NetworkModel = network
        super().__init__(*args, header_height=DATATABLE_HEADER_HEIGHT, **kwargs)

    def on_mount(self) -> None:
        """
        Initializes the DataTable and display data.
        """
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.expand = True
        self.update_display_columns()
        self.update_display_rows()

    def get_responsive_width(self, index: int) -> int:
        """
        Compute the responsive width for a column based on its index.

        Args:
            index (int): The index of the column.

        Returns:
            int: The computed width for the column.
        """
        if RESPONSIVE_COLUMNS[index]:
            not_resp_cols_w = sum(
                [
                    DATATABLE_MIN_WIDTH[i]
                    for i, b in enumerate(RESPONSIVE_COLUMNS)
                    if not b
                ]
            )
            cell_padding_w = 2 * len(RESPONSIVE_COLUMNS) * self.cell_padding
            space_w = self.r_renderable_width - not_resp_cols_w - cell_padding_w
            return max(
                int(space_w / (1.0 * sum(RESPONSIVE_COLUMNS))),
                DATATABLE_MIN_WIDTH[index],
            )
        return DATATABLE_MIN_WIDTH[index]

    def update_display_columns(self) -> None:
        """
        Display the DataTable columns.
        This method clears the existing columns and adds new ones.
        It should be called when the icon visibility changes or when the renderable width changes.
        """
        self.clear(True)
        for i, col in enumerate(DEFAULT_COLUMNS):
            content = Align(
                Text(f"{render_icon(col, self.r_show_icons)} {render_icon_label(col)}"),
                vertical="middle",
                height=DATATABLE_HEADER_HEIGHT,
            )
            self.add_column(content, key=col, width=self.get_responsive_width(i))

    def _justify_status(self) -> Literal["center", "left"]:
        """
        Determine the justification for the status column based on whether icons are shown.
        """
        return "center" if self.r_show_icons else "left"

    def update_display_row(self, conn: ConnectionModel) -> None:
        """
        Update a specific row in the DataTable with the connection data.

        Args:
            conn (ConnectionModel): The connection model containing the data to display.
        """
        for col in REFRESH_COLUMNS:
            content = Text(
                render_icon_or_label(conn[col], self.r_show_icons),
                justify=self._justify_status(),
            )
            self.update_cell(conn.key, col, content)

    def update_display_rows(self) -> None:
        """
        Create/Update/Delete the rows in the DataTable according to the current network connections.
        """
        for conn in self._network.connections:
            if self.get_row_or_default(conn.key) is None:
                self.add_row(
                    conn.pid,
                    conn.process_name,
                    conn.protocol,
                    conn.local_addr,
                    conn.remote_addr,
                    Text(
                        render_icon_or_label(conn.state, self.r_show_icons),
                        justify=self._justify_status(),
                    ),
                    conn.hostname,
                    key=conn.key,
                )
            else:
                self.update_display_row(conn)
        for conn in self._network.removed_connections:
            if self.get_row_or_default(conn.key) is not None:
                self.remove_row(conn.key)

    def watch_r_show_icons(self, old_show_icon: bool, new_show_icon: bool) -> None:
        """
        Watch for changes in the icon visibility and update the display columns accordingly.
        """
        if old_show_icon != new_show_icon:
            self.update_display_columns()

    def watch_r_renderable_width(self, old_width: int, new_width: int):
        """
        Watch for changes in the renderable width and update the display.
        """
        if old_width != new_width:
            self.update_display_columns()

    def update_display(self) -> None:
        """
        Update the DataTable display by refreshing rows.
        """
        self.update_display_rows()

    def get_row_or_default(
        self, row_key: str, default: Any = None
    ) -> list[CellType] | None:
        """
        Get a row from the DataTable by its key, or return a default value if it does not exist.

        Args:
            row_key (str): The key of the row to retrieve.
            default (Any): The default value to return if the row does not exist.

        Returns:
            list[CellType] | None: The row data if it exists, otherwise the default
        """
        try:
            res = self.get_row(cast(RowKey, row_key))
        except RowDoesNotExist:
            res = default
        return res
