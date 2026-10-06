import pandas as pd
import glob
import os


def add_label_and_overwrite(file_path, column_name, value):
    """
    Add column with one value
    """
    df = pd.read_csv(file_path)

    df[column_name] = value

    df.to_csv(file_path, index=False)

def merge_and_shuffle_csvs(input_folder, output_filename, shuffle=True):
    """
    Merge all CSV-Files of a Folder, randomize optional the order.
    """

    search_path = os.path.join(input_folder, "*.csv")
    csv_files = glob.glob(search_path)

    if not csv_files:
        print(f"No CSV-Files in {input_folder}.")
        return

    print(f"{len(csv_files)} Files found. Start Merging...")

    df_list = []
    for file in csv_files:
        df = pd.read_csv(file)
        df_list.append(df)
        print(f"Files loaded: {os.path.basename(file)}")

    merged_df = pd.concat(df_list, ignore_index=True)
    print(f"Merging finished. Columns: {len(merged_df)}")

    if shuffle:
        print("Randomize Columns...")
        merged_df = merged_df.sample(frac=1).reset_index(drop=True)

    merged_df.to_csv(output_filename, index=False)
    print(f"Finished! File saved at: {output_filename}")


if __name__ == "__main__":
    folder_path = "../../data/csvFiles/ready_for_train/train-server_52_and_122_v1_-_v3_BTC_and_NOBTC_WITH_OPENVPN_AND_SSTP_NO_TESTNET"

    output_file = "../../data/csvFiles/ready_for_train/train-server_52_and_122_v1_-_v3_BTC_and_NOBTC_WITH_OPENVPN_AND_SSTP_NO_TESTNET/all_merged.csv"

    merge_and_shuffle_csvs(folder_path, output_file, shuffle=True)