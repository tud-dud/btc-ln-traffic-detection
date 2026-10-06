import json
import numpy as np
import csv
import random
import os
from datetime import datetime


def find_server_port(data):
    """
    Heuristic to find the server port if port not specified
    1. Look at the very first packet of the first flow.
    2. If bytes > 0, the destination port is likely the server.
    3. If bytes < 0, the source port is likely the server.
    """
    if not data or not data[0].get('x_packets'):
        return None

    first_flow = data[0]
    first_packet = first_flow['x_packets'][0]

    try:
        raw_bytes = int(first_packet['bytes'])
        if raw_bytes > 0:
            return first_flow.get('port_dst')
        else:
            return first_flow.get('port_src')
    except (ValueError, KeyError):
        return first_flow.get('port_dst')  # Fallback


def extract_features_from_json(json_path, output_csv, min_sec:float=1, max_sec:float=10, manual_server_port=None, ndigits:int=2):
    """
    Read JSON-File with Package-Traffic and convert to Features in CSV.
    Uses auto-detection for the server port if manual_server_port is None.
    """
    if not os.path.exists(json_path):
        print(f"Error: File {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    # AUTO-DETECTION
    server_port = manual_server_port
    if server_port is None:
        server_port = find_server_port(data)
        print(f"Auto-detected Server Port for {os.path.basename(json_path)}: {server_port}")

    all_packets = []
    for flow in data:
        p_dst = flow.get('port_dst')
        p_src = flow.get('port_src')

        for pkt in flow.get('x_packets', []):
            try:
                raw_bytes = int(pkt['bytes'])
                size = abs(raw_bytes)

                # Direction logic
                is_outgoing = 0
                if p_dst == server_port:
                    if raw_bytes < 0:
                        # Server replied
                        is_outgoing = 1
                elif p_src == server_port:
                    if raw_bytes > 0:
                        # Server sent
                        is_outgoing = 1

                # Timestamp conversion
                ts = datetime.strptime(pkt['timestamp_start'], "%Y-%m-%d %H:%M:%S.%f").timestamp()
                all_packets.append({'time': ts, 'size': size, 'is_outgoing': is_outgoing})
            except (ValueError, KeyError, TypeError):
                continue

    # Sort all packets from all flows by time
    all_packets.sort(key=lambda x: x['time'])

    if not all_packets:
        print(f"Warning: No valid packets found in {json_path}.")
        return

    # CSV Header
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

    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        start_time = all_packets[0]['time']
        current_interval_packets = []
        current_target_duration = round(random.uniform(min_sec, max_sec), ndigits)

        for pkt in all_packets:
            if pkt['time'] < start_time + current_target_duration:
                current_interval_packets.append(pkt)
            else:
                if current_interval_packets:
                    stats = calculate_stats_json(current_interval_packets, current_target_duration, ndigits=ndigits)
                    writer.writerow(stats)

                start_time = pkt['time']
                current_target_duration = round(random.uniform(min_sec, max_sec), ndigits)
                current_interval_packets = [pkt]

        if current_interval_packets:
            stats = calculate_stats_json(current_interval_packets, current_target_duration, ndigits=ndigits)
            writer.writerow(stats)

    print(f"Finished. Features saved at: {output_csv}")


def calculate_stats_json(packets, target_duration, ndigits:int=2):
    """
    Calculates statistical features for a given list of packets.
    """

    sizes = [p['size'] for p in packets]
    times = [p['time'] for p in packets]

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
    # iats = np.diff(times) if len(times) > 1 else [0]
    # Calculate mean IAT
    #mean_iat = np.mean(iats) if len(iats) > 0 else 0
    # Calculate IAT variance
    #var_iat = np.var(iats) if len(iats) > 0 else 0
    # Calculate ratio of variance and mean IAT
    #var_mean_ratio = var_iat / mean_iat if mean_iat > 0 else 0
    # Calculate max idle gap
    #max_idle_gap = np.max(iats) if len(iats) > 0 else 0

    # Calculate outgoing/uploading bytes
    up_bytes = sum(p['size'] for p in packets if p['is_outgoing'])
    # Calculate incoming/downloading bytes
    down_bytes = sum(p['size'] for p in packets if not p['is_outgoing'])
    # Calculate ratio of up- and download
    ratio_up_down = up_bytes / down_bytes if down_bytes > 0 else up_bytes

    # Count packets under 100 bytes
    small_pkts = sum(1 for s in sizes if s < 100)
    # Calculate percentage share of small packets
    pct_small = small_pkts / packet_count if packet_count > 0 else 0

    # Count keep alives in duration
    keep_alives = sum(1 for s in sizes if s <= 66)
    # Calculate keep alives per min (sizes <= 66 Bytes)
    packets_smaller_equal_66b_per_min = (keep_alives / (duration_sec / 60)) if duration_sec > 0 else 0

    return [
        duration_sec, packet_count, total_bytes, median_size,
        p10, p25, p75, p90, size_var,
        ratio_up_down, pct_small, packets_smaller_equal_66b_per_min
    ]