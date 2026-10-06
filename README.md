# Network Traffic Analysis with Random Forest

This tool extracts up to 16 network features from PCAP or JSON files and uses a Random Forest model to train on them.

## Features
The scripts can extract the following characteristics from your data:
* `duration_sec`, `packet_count`, `total_bytes`
* `median_pkt_size`, `p10_size`, `p25_size`, `p75_size`, `p90_size`, `size_variance`
* `up_down_ratio` (Upload/Download ratio)
* `mean_iat`, `iat_variance`, `var_mean_iat_ratio` (Inter-Arrival Times),  `max_flow_idle_gap` (Deactivated due to synthetic data)
* `pct_packets_under_100b`, `packets_smaller_equal_66b_per_min`

## Workflow
1. **Extraction:** Convert raw network traffic files (`.pcap` or `.json`) into a structured CSV with the 12/16 features.
2. **Training:** Train a Random Forest classifier using the extracted data.
3. **Analysis:** Evaluate model performance (Accuracy, Feature Importance).

## Required Toolchain
Before running the scripts, ensure you have the following installed:
- **Python:** `>= 3.11`
- **Packet Capture Library:** `scapy` is used to read `.pcap` files. This requires a Packet Capture Library:
    - **Linux/macOS:** [libpcap](https://www.tcpdump.org/) (on macOS usually pre-installed)
        - Debian: `sudo apt install libpcap-dev`
        - Fedora: `sudo dnf install libpcap-devel`
    - **Windows:** [Npcap](https://npcap.com/) (Enable "Install Npcap in WinPcap API-compatible Mode" during installation)

## Run
1. If `./processed_CSVs` is empty, download the traffic from the repository to `./processed_CSVs` 
2. Place the processed CSVs in the `./processed_CSVs` folder. It should then look like this: `./processed_CSVs/negative_classes` and `./processed_CSVs/positive_classes`
3. Create a `.venv` and install requirements.
4. Run main.py. Press `y` at `Skip PCAP to CSV processing? (y/n)`. You can ignore the 'traces not found' error.
5. After execution, you will find the results in `./processed_CSVs/ml_setup/[Time-Window]/[BITCOIN OR LIGHTNING AS POSITIVE CLASS]/[WITH/WITHOUT P2P]/results`

## Run own Traffic
1. Organise your PCAP traffic within `./traces` into `./traces/negative_classes` and `./traces/positive_classes`. Review the Script if you want to use your own JSON traffic.
2. Create a folder for each traffic type (e.g. `./traces/positive_classes/bitcoin/name_[ipv4/ipv6].pcap`).
    - The server's IP address is used to calculate the upload/download ratio in the correct direction.
3. Run main.py again. The 'traces not found' error should disappear and the `.csv` files should be recreated. Press `n` at `Skip PCAP to CSV processing? (y/n)`. Warning: the processed_CSVs folder will be deleted and recreated. Save your results beforehand.

## Dataset
The published CSV files, which can be found under `./processed_CSVs/negative_classes` and `./processed_CSVs/positive_classes`, belong to the Combined Scale Time Window (0.001s - 10s) and provide a comprehensive overview, as they encompass both large and small observation periods.
