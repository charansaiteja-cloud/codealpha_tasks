import csv

import pytest
from scapy.all import (
    ARP,
    DNS,
    DNSQR,
    ICMP,
    IP,
    TCP,
    UDP,
    Ether,
    IPv6,
    Raw,
)

import sniffer


def test_ipv4_tcp_metadata():
    packet = Ether() / IP(src="192.0.2.1", dst="198.51.100.2") / TCP(sport=12345, dport=443)
    row = sniffer.parse_packet(packet)

    assert row["src"] == "192.0.2.1"
    assert row["dst"] == "198.51.100.2"
    assert row["src_port"] == "12345"
    assert row["dst_port"] == "443"
    assert row["ip_version"] == "IPv4"
    assert "TCP" in row["protocols"]
    assert row["length"] == len(packet)
    assert row["hex_preview"] == ""


def test_ipv6_udp_metadata():
    packet = Ether() / IPv6(src="2001:db8::1", dst="2001:db8::2") / UDP(sport=53000, dport=53)
    row = sniffer.parse_packet(packet)

    assert row["ip_version"] == "IPv6"
    assert row["src"] == "2001:db8::1"
    assert row["dst"] == "2001:db8::2"
    assert row["src_port"] == "53000"
    assert "UDP" in row["protocols"]


def test_arp_metadata():
    packet = Ether() / ARP(psrc="192.0.2.10", pdst="192.0.2.20")
    row = sniffer.parse_packet(packet)

    assert "ARP" in row["protocols"]
    assert row["src"] == "192.0.2.10"
    assert row["dst"] == "192.0.2.20"


def test_icmp_metadata_and_bounded_preview():
    packet = Ether() / IP() / ICMP() / Raw(load=b"ABCDEFGHIJKLMNOPQRST")
    row = sniffer.parse_packet(packet, preview_bytes=4)

    assert "ICMP" in row["protocols"]
    assert row["hex_preview"] == b"ABCD".hex()


def test_tcp_payload_is_never_previewed():
    packet = Ether() / IP() / TCP() / Raw(load=b"not-for-display")
    row = sniffer.parse_packet(packet, preview_bytes=16)

    assert row["hex_preview"] == ""


def test_dns_is_identified():
    packet = Ether() / IP() / UDP(sport=53000, dport=53) / DNS(rd=1, qd=DNSQR(qname="example.org"))
    row = sniffer.parse_packet(packet)

    assert "UDP" in row["protocols"]
    assert "DNS" in row["protocols"]
    assert row["dst_port"] == "53"


def test_csv_headers_and_packet_count(tmp_path):
    packets = [
        Ether() / IP(src="192.0.2.1", dst="192.0.2.2") / ICMP(),
        Ether() / IP(src="192.0.2.3", dst="192.0.2.4") / UDP(),
    ]
    output = tmp_path / "packets.csv"

    count = sniffer.write_packets_csv(output, packets)

    assert count == 2
    with output.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == list(sniffer.CSV_COLUMNS)
        rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["src"] == "192.0.2.1"


def test_empty_capture_still_writes_header(tmp_path):
    output = tmp_path / "empty.csv"

    count = sniffer.write_packets_csv(output, [])

    assert count == 0
    with output.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == list(sniffer.CSV_COLUMNS)
        assert list(reader) == []


def test_preview_limit_validation():
    packet = Ether() / IP() / ICMP()
    with pytest.raises(ValueError):
        sniffer.parse_packet(packet, preview_bytes=17)
    with pytest.raises(ValueError):
        sniffer.parse_packet(packet, preview_bytes=-1)


def test_csv_uses_correct_escaping(tmp_path):
    # CSV writer should quote fields containing commas and preserve their value.
    row = dict.fromkeys(sniffer.CSV_COLUMNS, "")
    row.update(
        timestamp="2026-01-01T00:00:00+00:00", src='host, "quoted"', protocols="IPv4/TCP", length=60
    )
    output = tmp_path / "escaping.csv"

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = sniffer.write_csv_header(handle)
        writer.writerow(row)

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["src"] == 'host, "quoted"'


def test_invalid_interface_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(sniffer, "available_interfaces", lambda: ["lo"])
    with pytest.raises(ValueError, match="not found"):
        sniffer.capture_to_csv("does-not-exist", 1, tmp_path / "out.csv")


def test_negative_count_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(sniffer, "available_interfaces", lambda: ["lo"])
    with pytest.raises(ValueError, match="count"):
        sniffer.capture_to_csv("lo", -1, tmp_path / "out.csv")


def test_timestamp_is_present():
    row = sniffer.parse_packet(Ether() / IP() / ICMP())
    assert row["timestamp"]
    assert row["timestamp"].endswith("+00:00")


def test_icmpv6_echo_request_is_identified():
    from scapy.all import ICMPv6EchoRequest

    packet = Ether() / IPv6() / ICMPv6EchoRequest()
    row = sniffer.parse_packet(packet)

    assert "IPv6" in row["protocols"]
    assert "ICMPv6" in row["protocols"]


def test_capture_reports_interrupt_with_partial_results(monkeypatch, tmp_path):
    packets = [
        Ether() / IP(src="192.0.2.1", dst="192.0.2.2") / TCP(),
        Ether() / IP(src="192.0.2.3", dst="192.0.2.4") / UDP(),
    ]

    def fake_sniff(**kwargs):
        for packet in packets:
            kwargs["prn"](packet)
        raise KeyboardInterrupt

    monkeypatch.setattr(sniffer, "available_interfaces", lambda: ["lo"])
    monkeypatch.setattr(sniffer, "sniff", fake_sniff)

    output = tmp_path / "interrupted.csv"
    with pytest.raises(sniffer.CaptureInterrupted) as excinfo:
        sniffer.capture_to_csv("lo", 0, output)

    assert excinfo.value.captured == 2
    assert excinfo.value.output_path == output

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2


def test_capture_passes_chain_cc_to_scapy(monkeypatch, tmp_path):
    captured_kwargs = {}

    def fake_sniff(**kwargs):
        captured_kwargs.update(kwargs)

    monkeypatch.setattr(sniffer, "available_interfaces", lambda: ["lo"])
    monkeypatch.setattr(sniffer, "sniff", fake_sniff)

    sniffer.capture_to_csv("lo", 0, tmp_path / "out.csv")

    assert captured_kwargs["chainCC"] is True
    assert captured_kwargs["store"] is False
    assert captured_kwargs["iface"] == "lo"


def test_capture_passes_bpf_filter(monkeypatch, tmp_path):
    captured_kwargs = {}

    def fake_sniff(**kwargs):
        captured_kwargs.update(kwargs)

    monkeypatch.setattr(sniffer, "available_interfaces", lambda: ["lo"])
    monkeypatch.setattr(sniffer, "sniff", fake_sniff)

    sniffer.capture_to_csv("lo", 1, tmp_path / "out.csv", bpf=" tcp port 443 ")

    assert captured_kwargs["filter"] == "tcp port 443"


def test_blank_bpf_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(sniffer, "available_interfaces", lambda: ["lo"])

    with pytest.raises(ValueError, match="BPF filter"):
        sniffer.capture_to_csv("lo", 1, tmp_path / "out.csv", bpf="   ")
