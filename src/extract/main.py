import os
import re

import analyze.analyze
import llmScripts.RandomForest
from extract_features import *
from extract_features_csv import *
from merge_csv import *
import shutil

# Main Class for task organization

def get_filenames_from_folder(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return []

    files = [
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]

    return files

def get_folders_in_folder(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return []

    folders = [
        f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))
    ]

    return folders

def process_traffic_trace_files(CSVs_FOLDER_PATH, files):
    os.mkdir(CSVs_FOLDER_PATH)
    for f in files:
        print(f" - Processing {f}...")
        if f.endswith(".json"):
            # Port = 443 here, cause I just have sstp as json traffic and sstp uses port 443.
            # Put your own json Traffic logic here
            extract_features_from_json(os.path.join(FOLDER_PATH, f),
                                       os.path.join(CSVs_FOLDER_PATH, f.replace(".json", ".csv")),
                                       min_sec=tw[0], max_sec=tw[1], manual_server_port=443, ndigits=N_DIGITS)
        elif f.endswith(".pcap"):
            # Search ipv4 Address
            ipv4_pattern = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
            match = re.search(ipv4_pattern, f)
            if not match:
                # Search ipv6 Address
                # Set :: and : in ipv6 Addresses (because windows forbid : in file naming)
                ipv6_f = f.replace(".", ":")
                ipv6_pattern = r"([0-9a-fA-F]{1,4}:){2,}[0-9a-fA-F]{1,4}"
                match = re.search(ipv6_pattern, ipv6_f)

            if not match:
                print(f"ERROR: No IP (v4 or v6) in {f} name")
                continue

            found_ip = match.group()
            extract_features(os.path.join(FOLDER_PATH, f),
                             os.path.join(CSVs_FOLDER_PATH, f.replace(".pcap", ".csv")), min_sec=tw[0],
                             max_sec=tw[1], manual_ip=found_ip, ndigits=N_DIGITS)

if __name__ == '__main__':
    N_DIGITS = 2
    # Add more Time windows if you want to analyse your own traffic
    TIME_WINDOWS = [[0.001, 10]]
    POS_FOLDER_PATH = "traces/positive_classes"
    NEG_FOLDER_PATH = "traces/negative_classes"
    PROCESSED_CSVS_FOLDER_PATH = "processed_CSVs"
    positive_classes_folders = get_folders_in_folder(POS_FOLDER_PATH)
    negative_classes_folders = get_folders_in_folder(NEG_FOLDER_PATH)

    skip = False
    if input("Skip PCAP to CSV processing? (y/n): ").lower() == "y":
        skip = True
    if not skip:
        print(f"Found {len(positive_classes_folders)} Positive classes folders.")
        for folder in positive_classes_folders:
            print(f" - {folder}")

        print(f"Found {len(negative_classes_folders)} Negative classes folders.")
        for folder in negative_classes_folders:
            print(f" - {folder}")


        print("Clear processed CSVs Folder...")
        shutil.rmtree(PROCESSED_CSVS_FOLDER_PATH, ignore_errors=True)
        os.mkdir(PROCESSED_CSVS_FOLDER_PATH)

        os.mkdir(os.path.join(PROCESSED_CSVS_FOLDER_PATH, "negative_classes"))
        os.mkdir(os.path.join(PROCESSED_CSVS_FOLDER_PATH, "positive_classes"))

        print("Processing Positive classes folders...")
        for folder in positive_classes_folders:
            FOLDER_PATH = os.path.join(POS_FOLDER_PATH, folder)
            files = get_filenames_from_folder(FOLDER_PATH)
            for tw in TIME_WINDOWS:
                print(f"Processing Timewindow {tw[0]} - {tw[1]} for folder {folder}...")
                if not os.path.exists(os.path.join(PROCESSED_CSVS_FOLDER_PATH, "positive_classes", f"{tw[0]} - {tw[1]}")):
                    os.mkdir(os.path.join(PROCESSED_CSVS_FOLDER_PATH, "positive_classes", f"{tw[0]} - {tw[1]}"))
                CSVs_FOLDER_PATH = os.path.join(PROCESSED_CSVS_FOLDER_PATH, "positive_classes", f"{tw[0]} - {tw[1]}",
                                                folder)
                process_traffic_trace_files(CSVs_FOLDER_PATH, files)

        print("Processing Negative classes folders...")
        for folder in negative_classes_folders:
            FOLDER_PATH = os.path.join(NEG_FOLDER_PATH, folder)
            files = get_filenames_from_folder(FOLDER_PATH)
            for tw in TIME_WINDOWS:
                print(f"Processing Timewindow {tw[0]} - {tw[1]} for folder {folder}...")
                if not os.path.exists(os.path.join(PROCESSED_CSVS_FOLDER_PATH, "negative_classes", f"{tw[0]} - {tw[1]}")):
                    os.mkdir(os.path.join(PROCESSED_CSVS_FOLDER_PATH, "negative_classes", f"{tw[0]} - {tw[1]}"))
                CSVs_FOLDER_PATH = os.path.join(PROCESSED_CSVS_FOLDER_PATH, "negative_classes", f"{tw[0]} - {tw[1]}", folder)
                process_traffic_trace_files(CSVs_FOLDER_PATH, files)

        print("All files processed to CSVs")
        print(f"Look {PROCESSED_CSVS_FOLDER_PATH}")

    print('Merge CSV files...')
    PROCESSED_CSVS_POSITIVE_FOLDER_PATH = "processed_CSVs/positive_classes"
    PROCESSED_CSVS_NEGATIVE_FOLDER_PATH = "processed_CSVs/negative_classes"
    if (not os.path.exists(PROCESSED_CSVS_POSITIVE_FOLDER_PATH)) and (not os.path.exists(PROCESSED_CSVS_NEGATIVE_FOLDER_PATH)):
        print(f"ERROR: {PROCESSED_CSVS_POSITIVE_FOLDER_PATH} or {PROCESSED_CSVS_NEGATIVE_FOLDER_PATH} does not exist.")
        exit(2)

    timewindow_folders_negative = get_folders_in_folder(PROCESSED_CSVS_NEGATIVE_FOLDER_PATH)
    timewindow_folders_positive = get_folders_in_folder(PROCESSED_CSVS_POSITIVE_FOLDER_PATH)

    for tw_folder in timewindow_folders_negative:
        folders = get_folders_in_folder(PROCESSED_CSVS_NEGATIVE_FOLDER_PATH + "/" + tw_folder)
        for folder in folders:
            print(f" - Merging {folder}...")
            merge_and_shuffle_csvs(PROCESSED_CSVS_NEGATIVE_FOLDER_PATH + "/" + tw_folder + "/" + folder,
                                   PROCESSED_CSVS_NEGATIVE_FOLDER_PATH + "/" + tw_folder + "/"
                                   + folder + "_merged.csv", shuffle=True)
            add_label_and_overwrite(
                PROCESSED_CSVS_NEGATIVE_FOLDER_PATH + "/" + tw_folder + "/" + folder + "_merged.csv",
                "TRAFFIC_TYPE", folder.upper())

    for tw_folder in timewindow_folders_positive:
        folders = get_folders_in_folder(PROCESSED_CSVS_POSITIVE_FOLDER_PATH + "/" + tw_folder)
        for folder in folders:
            print(f" - Merging {folder}...")
            merge_and_shuffle_csvs(os.path.join(PROCESSED_CSVS_POSITIVE_FOLDER_PATH, tw_folder, folder),
                                   os.path.join(PROCESSED_CSVS_POSITIVE_FOLDER_PATH, tw_folder, folder + "_merged.csv"),
                                   shuffle=True)
            add_label_and_overwrite(
                os.path.join(PROCESSED_CSVS_POSITIVE_FOLDER_PATH, tw_folder, folder + "_merged.csv"),
                "TRAFFIC_TYPE", folder.upper())

    print("Create Test Cases Folders...")
    ML_MERGED_CSVs_PATH = os.path.join(PROCESSED_CSVS_FOLDER_PATH, "ml_setup")
    shutil.rmtree(ML_MERGED_CSVs_PATH, ignore_errors=True)
    os.mkdir(ML_MERGED_CSVs_PATH)
    for tw in TIME_WINDOWS:
        print("Create " + str(tw[0]) + " - " + str(tw[1]) + "...")
        folder = os.path.join(ML_MERGED_CSVs_PATH, str(tw[0]) + " - " + str(tw[1]))
        os.mkdir(folder)

        BLACKLIST_WITHOUT_P2P = ["ethereum", "ipfs"]

        print("Create Lightning Positive Class Case...")
        lightning_class = os.path.join(folder, "lightning_pos")
        lightning_class_with_p2p = os.path.join(lightning_class, "with_p2p")
        lightning_class_without_p2p = os.path.join(lightning_class, "without_p2p")

        os.mkdir(lightning_class)
        os.mkdir(lightning_class_with_p2p)
        os.mkdir(lightning_class_without_p2p)
        os.mkdir(os.path.join(lightning_class_with_p2p, "negative_classes"))
        os.mkdir(os.path.join(lightning_class_without_p2p, "negative_classes"))

        tw_folder = str(tw[0]) + " - " + str(tw[1])
        folders_negative = get_folders_in_folder(os.path.join(PROCESSED_CSVS_NEGATIVE_FOLDER_PATH, tw_folder))

        # Without P2P Lightning Pos
        for folder_neg in folders_negative:
            if folder_neg not in BLACKLIST_WITHOUT_P2P:
                shutil.copy(os.path.join(PROCESSED_CSVS_NEGATIVE_FOLDER_PATH, tw_folder, folder_neg + "_merged.csv"),
                            os.path.join(lightning_class_without_p2p, "negative_classes", folder_neg + "_merged.csv"))
        shutil.copy(os.path.join(PROCESSED_CSVS_POSITIVE_FOLDER_PATH, tw_folder, "lightning_merged.csv"),
                    os.path.join(lightning_class_without_p2p, "lightning_merged.csv"))

        # Merge Without P2P Lightning Pos
        merge_and_shuffle_csvs(os.path.join(lightning_class_without_p2p, "negative_classes"),
                               os.path.join(lightning_class_without_p2p, "negative_merged.csv"), shuffle=True)
        # Add is_prot label
        add_label_and_overwrite(os.path.join(lightning_class_without_p2p, "negative_merged.csv"),
                                "is_prot", 0)
        add_label_and_overwrite(os.path.join(lightning_class_without_p2p, "lightning_merged.csv"),
                                "is_prot", 1)

        # With P2P Lightning Pos
        for folder_neg in folders_negative:
            shutil.copy(os.path.join(PROCESSED_CSVS_NEGATIVE_FOLDER_PATH, tw_folder, folder_neg + "_merged.csv"),
                        os.path.join(lightning_class_with_p2p, "negative_classes", folder_neg + "_merged.csv"))

        shutil.copy(os.path.join(PROCESSED_CSVS_POSITIVE_FOLDER_PATH, tw_folder, "bitcoin_merged.csv"),
                    os.path.join(lightning_class_with_p2p, "negative_classes", "bitcoin_merged.csv"))
        shutil.copy(os.path.join(PROCESSED_CSVS_POSITIVE_FOLDER_PATH, tw_folder, "lightning_merged.csv"),
                    os.path.join(lightning_class_with_p2p, "lightning_merged.csv"))

        # Merge Without P2P Lightning Pos
        merge_and_shuffle_csvs(os.path.join(lightning_class_with_p2p, "negative_classes"),
                               os.path.join(lightning_class_with_p2p, "negative_merged.csv"),
                               shuffle=True)
        # Add is_prot label
        add_label_and_overwrite(os.path.join(lightning_class_with_p2p, "negative_merged.csv"),
                                "is_prot", 0)
        add_label_and_overwrite(os.path.join(lightning_class_with_p2p, "lightning_merged.csv"),
                                "is_prot", 1)

        print("Create Bitcoin Positive Class Case...")
        bitcoin_class = os.path.join(folder, "bitcoin_pos")
        bitcoin_class_with_p2p = os.path.join(bitcoin_class, "with_p2p")
        bitcoin_class_without_p2p = os.path.join(bitcoin_class, "without_p2p")

        os.mkdir(bitcoin_class)
        os.mkdir(bitcoin_class_with_p2p)
        os.mkdir(bitcoin_class_without_p2p)
        os.mkdir(os.path.join(bitcoin_class_with_p2p, "negative_classes"))
        os.mkdir(os.path.join(bitcoin_class_without_p2p, "negative_classes"))

        # Without P2P Bitcoin Pos
        for folder_neg in folders_negative:
            if folder_neg not in BLACKLIST_WITHOUT_P2P:
                shutil.copy(os.path.join(PROCESSED_CSVS_NEGATIVE_FOLDER_PATH, tw_folder, folder_neg + "_merged.csv"),
                            os.path.join(bitcoin_class_without_p2p, "negative_classes", folder_neg + "_merged.csv"))
        shutil.copy(os.path.join(PROCESSED_CSVS_POSITIVE_FOLDER_PATH, tw_folder, "bitcoin_merged.csv"),
                    os.path.join(bitcoin_class_without_p2p, "bitcoin_merged.csv"))

        # Merge Without P2P Lightning Pos
        merge_and_shuffle_csvs(os.path.join(bitcoin_class_without_p2p, "negative_classes"),
                               os.path.join(bitcoin_class_without_p2p, "negative_merged.csv"), shuffle=True)
        # Add is_prot label
        add_label_and_overwrite(os.path.join(bitcoin_class_without_p2p, "negative_merged.csv"),
                                "is_prot", 0)
        add_label_and_overwrite(os.path.join(bitcoin_class_without_p2p, "bitcoin_merged.csv"),
                                "is_prot", 1)

        # With P2P Bitcoin Pos
        for folder_neg in folders_negative:
            shutil.copy(os.path.join(PROCESSED_CSVS_NEGATIVE_FOLDER_PATH, tw_folder, folder_neg + "_merged.csv"),
                        os.path.join(bitcoin_class_with_p2p, "negative_classes", folder_neg + "_merged.csv"))
        shutil.copy(os.path.join(PROCESSED_CSVS_POSITIVE_FOLDER_PATH, tw_folder, "bitcoin_merged.csv"),
                    os.path.join(bitcoin_class_with_p2p, "bitcoin_merged.csv"))
        shutil.copy(os.path.join(PROCESSED_CSVS_POSITIVE_FOLDER_PATH, tw_folder, "lightning_merged.csv"),
                    os.path.join(bitcoin_class_with_p2p, "negative_classes", "lightning_merged.csv"))

        # Merge Without P2P Lightning Pos
        merge_and_shuffle_csvs(os.path.join(bitcoin_class_with_p2p, "negative_classes"),
                               os.path.join(bitcoin_class_with_p2p, "negative_merged.csv"),
                               shuffle=True)
        # Add is_prot label
        add_label_and_overwrite(os.path.join(bitcoin_class_with_p2p, "negative_merged.csv"),
                                "is_prot", 0)
        add_label_and_overwrite(os.path.join(bitcoin_class_with_p2p, "bitcoin_merged.csv"),
                                "is_prot", 1)

    # Run Training
    for tw in TIME_WINDOWS:
        print(f"Run Random Forest for {tw[0]} - {tw[1]}")
        TW_FOLDER_PATH = os.path.join(ML_MERGED_CSVs_PATH, str(tw[0]) + " - " + str(tw[1]))
        BITCOIN_POS_WITH_P2P_FOLDER_PATH = os.path.join(TW_FOLDER_PATH, "bitcoin_pos", "with_p2p")
        BITCOIN_POS_WITHOUT_P2P_FOLDER_PATH = os.path.join(TW_FOLDER_PATH, "bitcoin_pos", "without_p2p")
        LIGHTNING_POS_WITH_P2P_FOLDER_PATH = os.path.join(TW_FOLDER_PATH, "lightning_pos", "with_p2p")
        LIGHTNING_POS_WITHOUT_P2P_FOLDER_PATH = os.path.join(TW_FOLDER_PATH, "lightning_pos", "without_p2p")
        # Create Results Folder
        for trainfolder in [BITCOIN_POS_WITHOUT_P2P_FOLDER_PATH, BITCOIN_POS_WITH_P2P_FOLDER_PATH,
                            LIGHTNING_POS_WITH_P2P_FOLDER_PATH, LIGHTNING_POS_WITHOUT_P2P_FOLDER_PATH]:
            print(f"Run {trainfolder}")
            results_folder = os.path.join(trainfolder, "results")
            os.mkdir(results_folder)
            # Create Model CSV
            merge_and_shuffle_csvs(trainfolder, os.path.join(trainfolder, "dataset.csv"), shuffle=True)
            # 0 - 11 Features, 13 Targets, 12 Real label (NOT IN ML!)
            llmScripts.RandomForest.run_random_forrest(os.path.join(trainfolder, "dataset.csv"), results_folder, 0, 11, 13, test_size_val=0.2)

            #Analyze Featrues
            features_to_analyze = ["total_bytes", "duration_sec", "packet_count"]
            for feature in features_to_analyze:
                analyze.analyze.analyze_performance(os.path.join(results_folder, "rf_predictions.csv"), "RF Prediction Prob", "is_prot", feature, results_folder)