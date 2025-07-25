import re
from math import log
from typing import TypedDict, Iterable, Mapping, Literal, Tuple, Generator, cast

from .constants import DEFAULT_COL_SORT, ALL_INTERFACE
from .network import get_connections, get_send_recv_bytes

ConnectionAttributes = Literal[
    "pid", "name", "protocol", "laddr", "raddr", "status", "ns"
]


class ConnectionData(TypedDict):
    """
    TypedDict representing the data of a network connection.
    """

    pid: str
    name: str
    protocol: Literal["TCP", "UDP"]
    laddr: str
    raddr: str
    status: str
    ns: str


class ConnectionModel:
    """
    Model representing a network connection.
    """

    def __init__(self, data):
        """
        Initialize the ConnectionModel with connection data.

        Args:
            data (dict[str, str]): Dict representing the connection data.

        Raises:
            ValueError: If the data does not contain the required keys.
        """
        self._data = ConnectionData(
            pid=data["pid"],
            name=data["name"],
            protocol=cast(Literal["TCP", "UDP"], data["protocol"]),
            laddr=data["laddr"],
            raddr=data["raddr"],
            status=data.get("status", ""),
            ns=data["ns"],
        )
        self._flag_updated: bool = True

    @property
    def pid(self):
        """
        The PID of the process that owns the connection.

        Returns:
            str: The PID of the connection.
        """
        return self._data["pid"]

    @property
    def process_name(self):
        """
        The name of the process that owns the connection.

        Returns:
            str: The name of the process.
        """
        return self._data["name"]

    @property
    def protocol(self):
        """
        The protocol of the connection.

        Returns:
            str: The protocol of the connection, either "TCP" or "UDP".
        """
        return self._data["protocol"]

    @property
    def local_addr(self):
        """
        The local address of the connection.

        Returns:
            str: The local address formatted as address:port.
        """
        return self._data["laddr"]

    @property
    def remote_addr(self) -> str:
        """
        The remote address of the connection.

        Returns:
            str: The remote address formatted as address:port.
        """
        return self._data["raddr"]

    @property
    def state(self) -> str:
        """
        The state of the connection.

        Returns:
            str: The state of the connection.
        """
        return self._data["status"]

    @property
    def hostname(self) -> str:
        """
        The hostname of the connection.

        Returns:
            str: The hostname of the connection.
        """
        return self._data["ns"]

    @property
    def should_remove(self) -> bool:
        """
        Check if the connection should be removed from the list.

        Returns:
            bool: True if the connection should be removed, False otherwise.
        """
        return not self._flag_updated

    @property
    def key(self) -> str:
        """
        Generate a unique key for the connection based on its attributes.

        Returns:
            str: A unique key for the connection.
        """
        return ConnectionModel.get_key(self._data)

    @staticmethod
    def get_key(conn: Mapping[str, str] | ConnectionData) -> str:
        """
        Generate a unique key for the connection based on its attributes.

        Args:
            conn (Mapping[str, str] | ConnectionData): The connection data.

        Returns:
            str: A unique key for the connection.
        """
        return f"{conn["pid"]}{conn["laddr"]}{conn["raddr"]}"

    def __getitem__(self, item: ConnectionAttributes) -> str | None:
        """
        Get the value of a specific attribute from the connection data.

        Args:
            item (ConnectionAttributes): The attribute to retrieve.

        Returns:
            str | None: The value of the attribute, or None if it does not exist.
        """
        return self._data.get(item)

    def update(self, new_data: dict[str, str]) -> None:
        """
        Update the connection status.

        Args:
            new_data (dict[str, str]): Dict representing the new state of the connection.
        """
        self._data["status"] = new_data.get("status", "")
        self._flag_updated = True

    def unset_flag(self) -> None:
        """
        Unset the flag indicating that the connection data has been updated.
        """
        self._flag_updated = False

    def __iter__(self) -> Generator[str]:
        """
        Iterate over the attributes of the ConnectionData instance.

        Yields:
            str: Values of the ConnectionData instance.
        """
        for val in self._data.values():
            yield val

    def __repr__(self) -> str:
        """
        Get a string representation of the ConnectionModel instance.

        Returns:
            str: String representation of the ConnectionModel instance.
        """
        return f"<ConnectionModel ({self.pid}, {self.process_name}, {self.local_addr}, {self.remote_addr}, {self.state})"


class NetworkIOModel:
    """
    Model representing network IO data for a specific interface.
    This model tracks the number of bytes sent and received, as well as the bandwidth
    in and out for the specified network interface.
    It provides methods to update the data and format the bandwidth in a human-readable way.
    """

    def __init__(self):
        """
        Initialize the NetworkIOModel instance.
        """
        self._bytes_sent: int = 0
        self._bytes_recv: int = 0
        self._timestamp: float = 0.0
        self._bandwidth_in: int = 0
        self._bandwidth_out: int = 0
        self._bytes_sent, self._bytes_recv, self._timestamp = get_send_recv_bytes(
            ALL_INTERFACE
        )

    @property
    def render_bandwidth_in(self) -> str:
        """
        The incoming bandwidth in a human-readable format.

        Returns:
            str: Human-readable string representation of incoming bandwidth.
        """
        return self._human_format(self._bandwidth_in)

    @property
    def render_bandwidth_out(self) -> str:
        """
        The outgoing bandwidth in a human-readable format.

        Returns:
            str: Human-readable string representation of outgoing bandwidth.
        """
        return self._human_format(self._bandwidth_out)

    @staticmethod
    def _human_format(
            nb_bytes: int,
            units: Tuple[int] = ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi"),
    ) -> str:
        """
        Format bytes into a human-readable format.

        Args:
            nb_bytes (int): Number of bytes.
            units (Tuple[int]): Tuple of units.

        Returns:
            str: Human-readable string representation of bytes.
        """
        if nb_bytes == 0:
            return "0 B"
        exp = int(log(nb_bytes, 1024))
        return f"{nb_bytes // 1024 ** exp} {units[exp]}B"

    def update_data(self, interface: str) -> None:
        """
        Update the network IO data for a specific interface.
        This method calculates the bandwidth in and out based on the bytes sent and received
        since the last update.

        Params:
            interface (str): The network interface.
        """
        net_io = get_send_recv_bytes(interface)
        self._bandwidth_in = int(
            (net_io[0] - self._bytes_sent) / (net_io[2] - self._timestamp)
        )
        self._bandwidth_out = int(
            (net_io[1] - self._bytes_recv) / (net_io[2] - self._timestamp)
        )
        self._bytes_sent, self._bytes_recv, self._timestamp = net_io


class Metrics:
    """
    Model representing network connection metrics.
    """

    def __init__(self):
        """
        Initialize the Metrics with zero values.
        """
        self._actives: int = 0
        self._listening: int = 0
        self._nb_conns: int = 0

    @property
    def nb_actives(self) -> int:
        """
        Get the number of active connections.

        Returns:
            int: Number of active connections.
        """
        return self._actives

    @property
    def nb_listening(self) -> int:
        """
        Get the number of listening connections.

        Returns:
            int: Number of listening connections.
        """
        return self._listening

    @property
    def nb_connections(self) -> int:
        """
        Get the total number of connections.

        Returns:
            int: Total number of connections.
        """
        return self._nb_conns

    def reset(self) -> None:
        """
        Reset all metrics to zero.
        """
        self._actives = 0
        self._listening = 0
        self._nb_conns = 0

    def update(self, conn: ConnectionModel) -> None:
        """
        Update metrics based on a connection.

        Args:
            conn (ConnectionModel): Connection to update metrics for.
        """
        if conn.state == "ESTABLISHED":
            self._actives += 1
        if conn.state == "LISTEN":
            self._listening += 1
        self._nb_conns += 1

    def __repr__(self) -> str:
        """
        Get a string representation of the metrics instance.

        Returns:
            str: String representation of the metrics instance.
        """
        return (
            f"<Metrics ({self.nb_connections}, {self.nb_actives}, {self.nb_listening})"
        )


class NetworkModel:
    """
    Model that represent the network state.
    """

    def __init__(self):
        """
        Initialize the NetworkModel with empty connections and metrics.
        """
        self._all_conns: dict[str:ConnectionModel] = {}
        self._pattern: re.Pattern[str] = re.compile("")
        self._sort_mode: str = DEFAULT_COL_SORT
        self._conns: list[ConnectionModel] = []
        self._removed_conns: list[ConnectionModel] = []
        self._metrics: Metrics = Metrics()

    @property
    def metrics(self) -> Metrics:
        """
        The metrics instance.

        Returns:
            Metrics: Instance of the Metrics class.
        """
        return self._metrics

    @property
    def connections(self) -> list[ConnectionModel]:
        """
        The list of filtered and sorted connections.

        Returns:
            list[ConnectionModel]: List of filtered and sorted connections.
        """
        return self._conns

    @property
    def removed_connections(self) -> list[ConnectionModel]:
        """
        The list of removed connections for updating the datatable.

        Returns:
            list[ConnectionModel]: List of removed connections for updating the datatable.
        """
        return self._removed_conns

    def update_data(self) -> None:
        """
        Update the connections data by fetching all connections and updating metrics.
        """
        self.metrics.reset()
        for conn_data in get_connections():
            key = ConnectionModel.get_key(conn_data)
            if self._filter(conn_data.values()):
                if key not in self._all_conns:
                    self._all_conns[key] = ConnectionModel(conn_data)
                    self.connections.append(self._all_conns[key])
                else:
                    self._all_conns[key].update(conn_data)
                self.metrics.update(self._all_conns[key])
        self._removed_conns = [c for c in self.connections if c.should_remove]
        for conn in self._removed_conns:
            self.connections.remove(conn)
            self._all_conns.pop(conn.key)
        self.connections.sort(key=lambda x: x[self._sort_mode].lower())
        for conn in self.connections:
            conn.unset_flag()

    def _filter(self, attributes: Iterable[str] | ConnectionModel) -> bool:
        """
        Filter connections based on the current regex pattern on any ConnectionModel data attribute.

        Args:
            attributes (Iterable[str] | ConnectionModel): .

        Returns:
            bool: True if the connection matches the pattern, False otherwise.
        """
        return any([self._pattern.match(attr) for attr in attributes])

    def _filter_conns(self, conns: Iterable[ConnectionModel]):
        """
        Filter connections and update the internal connection lists.

        Args:
            conns (Iterable[ConnectionModel]): Iterable of all connections to filter.
        """
        self._conns = []
        self._removed_conns = []
        for c in conns:
            if self._filter(c):
                self._conns.append(c)
            else:
                self._removed_conns.append(c)

    def filter(self, pattern: str) -> None:
        """
        Filter connections based on a regex pattern.

        Args:
            pattern (str): A regex pattern.
        """
        self._pattern = re.compile(pattern, re.IGNORECASE)
        self._filter_conns(self._all_conns.values())

    def reorder(self, sort_mode: ConnectionAttributes) -> None:
        """
        Reorder connections based on a specified ConnectionData attribute.

        Args:
            sort_mode (str): A specified ConnectionData attribute
        """
        self.connections.sort(key=lambda x: x[sort_mode].lower())
        self._sort_mode = sort_mode
