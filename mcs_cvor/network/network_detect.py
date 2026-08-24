"""Network interface detection using psutil."""
from typing import List, Dict
import psutil
import socket


def get_local_interfaces() -> List[Dict[str, str]]:
    """Return list of dicts with ip, netmask, gateway for each NIC."""
    interfaces = []
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    gateways = _get_gateways()

    for iface, addr_list in addrs.items():
        if iface not in stats or not stats[iface].isup:
            continue
        for addr in addr_list:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                interfaces.append({
                    "interface": iface,
                    "ip": addr.address,
                    "netmask": addr.netmask or "",
                    "gateway": gateways.get(iface, gateways.get("default", "")),
                })
    return interfaces


def _get_gateways() -> Dict[str, str]:
    result = {}
    try:
        # Use netifaces-style fallback via socket
        import subprocess
        import platform
        if platform.system() == "Windows":
            out = subprocess.check_output(["route", "print", "0.0.0.0"], text=True, timeout=5)
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 3 and parts[0] == "0.0.0.0":
                    result["default"] = parts[2]
                    break
        else:
            out = subprocess.check_output(["ip", "route"], text=True, timeout=5)
            for line in out.splitlines():
                if line.startswith("default"):
                    parts = line.split()
                    if "via" in parts:
                        result["default"] = parts[parts.index("via") + 1]
                    break
    except Exception:
        pass
    return result
