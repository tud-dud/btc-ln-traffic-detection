import scapy.all as scapy
import numpy as np
import csv
import random
import os

def get_packet_src(pkt):
    """Get Source-IP, IPv4 or IPv6"""
    if pkt.haslayer(scapy.IP):
        return pkt[scapy.IP].src
    elif pkt.haslayer(scapy.IPv6):
        return pkt[scapy.IPv6].src
    return None

def extract_features(pcap_path, output_csv, min_sec:float=10, max_sec:float=600, manual_ip=None, ndigits:int=2):
    """
    Parses a PCAP file and extracts network features in random time intervals.
    The intervals are chosen sequentially and randomly between 10 and 600 seconds.
    """
    if not os.path.exists(pcap_path):
        print(f"Error: File {pcap_path} not found.")
        return

    # header = [
    #     "duration_sec", "packet_count", "total_bytes", "median_pkt_size",
    #     "p10_size", "p25_size", "p75_size", "p90_size", "size_variance",
    #     "up_down_ratio", "mean_iat", "iat_variance", "var_mean_iat_ratio",
    #     "pct_packets_under_100b", "max_flow_idle_gap", "keep_alive_per_min"
    # ]
    header = [
        "duration_sec", "packet_count", "total_bytes", "median_pkt_size",
        "p10_size", "p25_size", "p75_size", "p90_size", "size_variance",
        "up_down_ratio", "pct_packets_under_100b", "packets_smaller_equal_66b_per_min"
    ]

    reader = scapy.PcapReader(pcap_path)
    local_ip = manual_ip

    if local_ip is None:
        for pkt in reader:
            if pkt.haslayer(scapy.IP):
                local_ip = pkt[scapy.IP].src
                print(f"Auto-detected: Setting local IP to {local_ip}")
                break
            elif pkt.haslayer(scapy.IPv6):
                local_ip = pkt[scapy.IPv6].src
                print(f"Auto-detected: Setting local IP (IPv6) to {local_ip}")
                break
        reader.close()

    reader = scapy.PcapReader(pcap_path)

    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        current_interval_packets = []
        try:
            first_pkt = next(reader)
            start_time = float(first_pkt.time)
            current_interval_packets.append(first_pkt)
        except StopIteration:
            print("Error: PCAP file is empty.")
            return

        current_target_duration = round(random.uniform(min_sec, max_sec), ndigits)

        for pkt in reader:
            pkt_time = float(pkt.time)

            if pkt_time < start_time + current_target_duration:
                current_interval_packets.append(pkt)
            else:
                stats = calculate_stats(current_interval_packets, current_target_duration, local_ip, ndigits=ndigits)
                writer.writerow(stats)

                start_time = pkt_time
                current_target_duration = round(random.uniform(min_sec, max_sec), ndigits)
                current_interval_packets = [pkt]

        if current_interval_packets:
            stats = calculate_stats(current_interval_packets, current_target_duration, local_ip, ndigits=ndigits)
            writer.writerow(stats)

    print(f" - Extraction finished. Data saved at: {output_csv}")

def calculate_stats(packets, target_duration, local_ip, ndigits:int=2):
    """
    Calculates statistical features for a given list of packets.
    """
    sizes = [p.wirelen for p in packets]
    times = [float(p.time) for p in packets]

    # Count Packages
    packet_count = len(packets)
    # Calculate total Bytes
    total_bytes = sum(sizes)
    # Set duration sec
    duration_sec = round(float(target_duration), ndigits)

    # Calculate Median Size
    median_size = np.median(sizes)
    # Calculate Percentiles
    p10, p25, p75, p90 = np.percentile(sizes, [10, 25, 75, 90])
    # Calculate Size Variance
    size_var = np.var(sizes)

    # Calculate IATS for each packet
    iats = np.diff(times) if len(times) > 1 else [0]
    # Calculate mean IAT
    #mean_iat = np.mean(iats) if len(iats) > 0 else 0
    # Calculate IAT variance
    #var_iat = np.var(iats) if len(iats) > 0 else 0
    # Calculate ratio of variance and mean IAT
    #var_mean_ratio = var_iat / mean_iat if mean_iat > 0 else 0
    # Calculate max idle gap
    #max_idle_gap = np.max(iats) if len(iats) > 0 else 0

    up_bytes = 0
    down_bytes = 0
    # Calculate outgoing/uploading and incoming/downloading bytes
    for p in packets:
        src = get_packet_src(p)
        if src == local_ip:
            # outgoing
            up_bytes += len(p)
        else:
            # incoming
            down_bytes += len(p)

    # Calculate ratio of up- and download
    ratio_up_down = up_bytes / down_bytes if down_bytes > 0 else up_bytes

    # Count packets under 100 bytes
    small_pkts = sum(1 for s in sizes if s < 100)
    # Calculate percentage share of small packets
    pct_small = small_pkts / packet_count if packet_count > 0 else 0

    # Keep-Alive estimation (packets <= 66 bytes per minute)
    keep_alives = sum(1 for s in sizes if s <= 66)
    # Calculate keep alives per min (sizes <= 66 Bytes)
    packets_smaller_equal_66b_per_min = (keep_alives / (duration_sec / 60)) if duration_sec > 0 else 0

    return [
        duration_sec, packet_count, total_bytes, median_size,
        p10, p25, p75, p90, size_var,
        ratio_up_down, pct_small, packets_smaller_equal_66b_per_min
    ]