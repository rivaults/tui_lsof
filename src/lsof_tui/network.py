"""Helper functions for gathering network connections."""

from subprocess import check_output, CalledProcessError, DEVNULL
import psutil
import socket
from time import time

from textual import log

from .constants import ALL_INTERFACE


def _get_lsof_output() -> str:
    """
    Get the output of the lsof command.
    """
    output = None
    try:
        output = check_output(
            " ".join(
                ["lsof", "-nP", "-a", "-i4", "-i6", "-itcp", "-iudp", "-FcpPnT", "-Q"]
            ),
            text=True,
            stderr=DEVNULL,
            shell=True,
        )
    except FileNotFoundError:
        raise RuntimeError("lsof command not found. Please install lsof.")
    except CalledProcessError:
        pass
    return output if output is not None else ""


def _set_addr(d: dict[str, str], addr: str, sep: str = "->") -> None:
    """
    Set the local and remote addresses in the dictionary from a string.

    Args:
        d (dict[str,str]): The dictionary to update.
        addr (str): The connection string to parse (laddr:lport->raddr:rport).
        sep (str): The separator between local and remote addresses. Defaults to '->'.
    """
    if sep in addr:
        d["laddr"], d["raddr"] = map(str.strip, addr.split(sep, 1))
    else:
        d["laddr"] = addr.strip()
        d["raddr"] = ""


def _has_described_connection(line: str) -> bool:
    """
    Check if a connection has been described.

    Args:
        line (str): The line from the lsof output.

    Returns:
        bool: True if the line terminate the connection description, False otherwise.
    """
    return line.startswith("TQS")


def _set_attr_from_line(current: dict[str, str], line: str) -> None:
    """
    Set attributes in the current connection based on the line from lsof output.

    Args:
        current (dict[str, str]): The current connection to update.
        line (str): The line from the lsof output.
    """
    if line.startswith("p"):
        current["pid"] = line[1:]
    elif line.startswith("c"):
        current["name"] = line[1:]
    elif line.startswith("P"):
        current["protocol"] = line[1:]
    elif line.startswith("n"):
        _set_addr(current, line[1:])
    elif line.startswith("TST"):
        current["status"] = line[4:]


def _copy_connection(conn: dict[str, str]) -> dict[str, str]:
    """
    Create a copy of the connection dictionary with only relevant attributes.

    Args:
        conn (dict[str, str]): The connection to copy.

    Returns:
        dict[str, str]: A new dictionary with the 'pid' and 'name' attributes.
    """
    return {
        "pid": conn["pid"],
        "name": conn["name"],
    }


def _get_lsof_conns() -> list[dict[str, str]]:
    """
    Get the network connections from the lsof command output.

    Returns:
        list[dict[str, str]]: A list of dictionaries representing network connections.
    """
    conns = []
    curr = {}
    for line in _get_lsof_output().splitlines():
        _set_attr_from_line(curr, line)
        if _has_described_connection(line):
            conns.append(curr)
            curr = _copy_connection(curr)
    return conns


def _get_addr(addr_port: str) -> str:
    """
    Extract the address from a string that contain an address and a port (addr:port).

    Args:
        addr_port (str): The address and port string

    Returns:
        str: The address part of the string.
    """
    return addr_port.split(":")[0]


def _get_hostname_from_conn(remote: str) -> str:
    """
    Resolve the hostname from a remote address.

    Args:
        remote (str): The remote address in the format 'addr:port'.

    Returns:
        str: The hostname if resolved, otherwise an empty string.
    """
    res = None
    try:
        res, *_ = socket.gethostbyaddr(_get_addr(remote))
    except (socket.herror, socket.gaierror) as e:
        log.debug(f"Error resolving {_get_addr(remote)} {e}")
    except OSError as e:
        log.debug(f"OSError : {e}")
    if res is None:
        return ""
    if "." in res:
        return ".".join(res.rsplit(".", maxsplit=2)[1:])
    return res


def get_connections() -> list[dict[str, str]]:
    """
    Get the network connections from the lsof command output and resolve hostnames.

    Returns:
        list[dict[str, str]]: A list of dictionaries representing network connections.
    """
    results = _get_lsof_conns()
    for conn in results:
        conn["ns"] = _get_hostname_from_conn(conn["raddr"])
    return results


def get_send_recv_bytes(interface: str) -> tuple[int, int, float]:
    """
    Get the number of bytes sent and received on a specific network interface and a timestamp.

    Args:
        interface (str): The name of the network interface. Use 'ALL' to get total
                            bytes for all interfaces.

    Returns:
        tuple[int, int, float]: A tuple containing the number of bytes sent, the number
                                of bytes received, and the timestamp of the measurement.
    """
    timestamp = time()
    net_io_tmp = psutil.net_io_counters(pernic=interface != ALL_INTERFACE)
    if interface != ALL_INTERFACE:
        net_io_tmp = net_io_tmp[interface]
    return net_io_tmp.bytes_sent, net_io_tmp.bytes_recv, timestamp
