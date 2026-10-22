#!/usr/bin/env python3
"""Authorized, metadata-first network sniffer using Scapy."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, TextIO

try:
    from scapy.all import (
        ARP,
        DNS,
        ICMP,
        ICMPv6Unknown,
        IP,
        IPv6,
        TCP,
        UDP,
        get_if_list,
        sniff,
    )
    from scapy.error import Scapy_Exception
except ImportError:
    print(
        "Scapy is not installed. Activate your virtual environment and run "
        "'python -m pip install -r requirements.txt'.",
        file=sys.stderr,
    )
    raise SystemExit(2)


CSV_COLUMNS = (
    "timestamp",
    "src",
    "dst",
    "src_port",
    "dst_port",
    "ip_version",
    "protocols",
    "length",
    "hex_preview",
)

MAX_PREVIEW_BYTES = 16


class CaptureInterrupted(Exception):
    """Raised when the operator stops a capture with Ctrl+C.

    The partial capture is already flushed to disk when this is raised.
    """

    def __init__(self, captured: int, output_path: Path) -> None:
        super().__init__(captured)
        self.captured = captured
        self.output_path = output_path


def parse_packet(packet, preview_bytes: int = 0) -> dict:
    """Convert a Scapy packet into a stable, privacy-conscious metadata row.

    Hex previews are deliberately restricted to ICMP/ICMPv6 payloads.
    TCP, UDP, and DNS application data are never previewed.
    """
    if not 0 <= preview_bytes <= MAX_PREVIEW_BYTES:
        raise ValueError(
            f"preview_bytes must be between 0 and {MAX_PREVIEW_BYTES}"
        )

    src = dst = ""
    src_port = dst_port = ""
    ip_version = ""
    protocols: list[str] = []

    if IP in packet:
        layer = packet[IP]
        src, dst = layer.src, layer.dst
        ip_version = "IPv4"
        protocols.append("IPv4")
    elif IPv6 in packet:
        layer = packet[IPv6]
        src, dst = layer.src, layer.dst
        ip_version = "IPv6"
        protocols.append("IPv6")
    elif ARP in packet:
        layer = packet[ARP]
        src, dst = layer.psrc, layer.pdst
        protocols.append("ARP")

    if TCP in packet:
        transport = packet[TCP]
        src_port, dst_port = str(transport.sport), str(transport.dport)
        protocols.append("TCP")
    elif UDP in packet:
        transport = packet[UDP]
        src_port, dst_port = str(transport.sport), str(transport.dport)
        protocols.append("UDP")

    if ICMP in packet:
        protocols.append("ICMP")

    # Scapy uses several concrete ICMPv6 classes rather than a public
    # ICMPv6 base class with the same name in every version.
    icmpv6_layer = next(
        (
            packet.getlayer(layer)
            for layer in packet.layers()
            if layer.__name__.startswith("ICMPv6")
        ),
        None,
    )
    if icmpv6_layer is not None:
        protocols.append("ICMPv6")

    if DNS in packet:
        protocols.append("DNS")

    # Include Ethernet-only or other packets without an identified network layer.
    if not protocols:
        protocols.append("OTHER")

    packet_time = getattr(packet, "time", None)
    if packet_time is None:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    else:
        timestamp = datetime.fromtimestamp(
            float(packet_time), tz=timezone.utc
        ).isoformat(timespec="milliseconds")

    hex_preview = ""
    if preview_bytes and (ICMP in packet or icmpv6_layer is not None):
        if ICMP in packet:
            payload = packet[ICMP].payload
        else:
            payload = icmpv6_layer.payload

        # Only a bounded ICMP/ICMPv6 payload prefix can be displayed.
        if payload and payload.__class__.__name__ != "NoPayload":
            hex_preview = bytes(payload)[:preview_bytes].hex()

    return {
        "timestamp": timestamp,
        "src": str(src),
        "dst": str(dst),
        "src_port": src_port,
        "dst_port": dst_port,
        "ip_version": ip_version,
        "protocols": "/".join(protocols),
        "length": len(packet),
        "hex_preview": hex_preview,
    }


def write_csv_header(handle: TextIO) -> csv.DictWriter:
    """Write the fixed CSV header and return a configured writer."""
    writer = csv.DictWriter(
        handle,
        fieldnames=CSV_COLUMNS,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    return writer


def write_packets_csv(
    output_path: str | Path,
    packets: Iterable,
    preview_bytes: int = 0,
) -> int:
    """Write metadata rows from an iterable; useful for offline processing."""
    count = 0
    with Path(output_path).open("w", newline="", encoding="utf-8") as handle:
        writer = write_csv_header(handle)
        for packet in packets:
            writer.writerow(parse_packet(packet, preview_bytes))
            count += 1
    return count


def available_interfaces() -> list[str]:
    """Return interfaces known to Scapy."""
    return sorted(set(get_if_list()))


def capture_to_csv(
    interface: str,
    count: int,
    output_path: str | Path,
    preview_bytes: int = 0,
) -> int:
    """Capture packets without retaining the packet list in memory."""
    interfaces = available_interfaces()
    if interface not in interfaces:
        choices = ", ".join(interfaces) if interfaces else "(none detected)"
        raise ValueError(
            f"Interface {interface!r} was not found. Available: {choices}"
        )
    if count < 0:
        raise ValueError("Packet count must be zero or greater.")
    if not 0 <= preview_bytes <= MAX_PREVIEW_BYTES:
        raise ValueError(
            f"Preview size must be between 0 and {MAX_PREVIEW_BYTES} bytes."
        )

    captured = 0
    output_path = Path(output_path)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = write_csv_header(handle)

        def handle_packet(packet) -> None:
            nonlocal captured
            row = parse_packet(packet, preview_bytes)
            writer.writerow(row)
            handle.flush()
            captured += 1
            print(format_packet(row))

        try:
            # Scapy count=0 means unlimited. store=False avoids accumulating
            # packets. chainCC=True lets Ctrl+C reach our own handler.
            sniff(
                iface=interface,
                count=count,
                prn=handle_packet,
                store=False,
                chainCC=True,
            )
        except KeyboardInterrupt:
            raise CaptureInterrupted(captured, output_path) from None

    return captured


def format_packet(row: dict) -> str:
    """Format one metadata row for readable terminal output."""
    endpoints = f"{row['src']} -> {row['dst']}"
    if row["src_port"] or row["dst_port"]:
        endpoints += f" ({row['src_port']} -> {row['dst_port']})"

    result = (
        f"{row['timestamp']} | {row['protocols']} | {endpoints} | "
        f"{row['length']} bytes"
    )
    if row["hex_preview"]:
        result += f" | ICMP payload prefix: {row['hex_preview']}"
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Metadata-first packet sniffer for networks you are authorized "
            "to monitor."
        )
    )
    parser.add_argument(
        "-i", "--interface",
        help="Interface to monitor (for example, eth0 or wlan0).",
    )
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=20,
        help="Maximum packets to capture; use 0 for continuous capture (default: 20).",
    )
    parser.add_argument(
        "-o", "--output",
        default="packets.csv",
        help="CSV output path (default: packets.csv).",
    )
    parser.add_argument(
        "--list-interfaces",
        action="store_true",
        help="List interfaces visible to Scapy and exit.",
    )
    parser.add_argument(
        "--hex-preview",
        type=int,
        default=0,
        metavar="BYTES",
        help=(
            "Optional ICMP/ICMPv6 payload prefix, 1-16 bytes. "
            "TCP/UDP/DNS payloads are never previewed."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_interfaces:
        interfaces = available_interfaces()
        if not interfaces:
            print("No interfaces detected.")
            return 1
        print("\n".join(interfaces))
        return 0

    if not args.interface:
        parser.error("--interface is required unless --list-interfaces is used")
    if args.count < 0:
        parser.error("--count must be zero or greater")
    if not 0 <= args.hex_preview <= MAX_PREVIEW_BYTES:
        parser.error("--hex-preview must be between 0 and 16 bytes")

    print(f"Interface: {args.interface}")
    print(f"Packet limit: {'unlimited' if args.count == 0 else args.count}")
    print(f"CSV output: {args.output}")
    print(f"ICMP preview: {args.hex_preview} byte(s)")
    print("Monitoring authorized traffic only. Press Ctrl+C to stop.")

    try:
        total = capture_to_csv(
            args.interface, args.count, args.output, args.hex_preview
        )
    except CaptureInterrupted as exc:
        print(
            f"\nCapture interrupted after {exc.captured} packet(s). "
            f"CSV saved to: {exc.output_path}"
        )
        return 130
    except KeyboardInterrupt:
        print(f"\nCapture interrupted. CSV saved to: {args.output}")
        return 130
    except PermissionError:
        print(
            "Permission denied. Check capture permissions for your interface "
            "and output directory. See README.md.",
            file=sys.stderr,
        )
        return 1
    except (ValueError, OSError, Scapy_Exception) as exc:
        print(f"Capture error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected capture error ({type(exc).__name__}): {exc}",
              file=sys.stderr)
        return 1

    if total == 0:
        print("Capture finished; no packets were observed.")
    else:
        print(f"Capture finished. Packets recorded: {total}")
    print(f"CSV saved to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
