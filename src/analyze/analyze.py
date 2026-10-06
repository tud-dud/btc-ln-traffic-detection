import os.path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sympy import true


def analyze_performance_by_feature():
    """
    Analyze Features
    """
    # Get file path and load data
    file_path = input("Enter path to predictions CSV: ").strip()
    try:
        df = pd.read_csv(file_path, low_memory=False)
    except FileNotFoundError:
        print(f"Error: {file_path} not found")
        return

    # Select relevant columns from the dataframe
    print("\nAvailable columns:", df.columns.tolist())
    pred_col = input("Enter the Prediction Probability column name: ").strip()
    target_col = input("Enter the name of the true target column: ").strip()
    feature_col = input("Enter the feature column to analyze: ").strip()

    # Define classification threshold
    try:
        threshold = float(input("Enter classification threshold (default 0.5): ") or 0.5)
    except ValueError:
        threshold = 0.5

    # remove nans and ensure numeric features
    df_test = df.dropna(subset=[pred_col]).copy()
    df_test[feature_col] = pd.to_numeric(df_test[feature_col], errors='coerce')
    df_test = df_test.dropna(subset=[feature_col])

    # remove top 1% outliers to improve visualization (optional)
    clip_outliers = input("Exclude top 1% outliers? (y/n): ").lower() == 'y'
    if clip_outliers:
        upper_limit = df_test[feature_col].quantile(0.99)
        df_test = df_test[df_test[feature_col] <= upper_limit]

    # Calculate binary predictions and correctness
    df_test['Prediction'] = (df_test[pred_col] >= threshold).astype(int)
    df_test['Is_Correct'] = (df_test['Prediction'] == df_test[target_col]).astype(int)

    # Bin the feature values into intervals
    num_bins = 15
    f_min, f_max = df_test[feature_col].min(), df_test[feature_col].max()
    bins = np.linspace(f_min, f_max, num_bins + 1)
    df_test['Bin_Interval'] = pd.cut(df_test[feature_col], bins=bins, include_lowest=True)

    # Group by bins and calculate accuracy and sample counts
    bin_analysis = df_test.groupby('Bin_Interval', observed=True)['Is_Correct'].agg(['mean', 'count']).reset_index()
    bin_analysis.columns = ['Interval', 'Accuracy', 'Sample_Count']

    # Helper function to format axis labels based on data scale/type
    def format_bin_label(interval):
        left, right = interval.left, interval.right
        if f_min >= 0 and left < 0: left = 0
        use_sci = (abs(right) < 0.01 and right != 0)
        is_int = np.issubdtype(df_test[feature_col].dtype, np.integer) or all(df_test[feature_col] % 1 == 0)
        if use_sci:
            return f"{left:.2e} to {right:.2e}"
        elif is_int:
            return f"{int(round(left))} to {int(round(right))}"
        else:
            return f"{left:.4f} to {right:.4f}"

    bin_analysis['Bin_Label'] = bin_analysis['Interval'].apply(format_bin_label)

    # Dynamic Y
    y_min_data = bin_analysis['Accuracy'].min()
    y_max_data = bin_analysis['Accuracy'].max()
    overall_acc = df_test['Is_Correct'].mean()

    all_y_values = [y_min_data, y_max_data, overall_acc]
    current_min = min(all_y_values)
    current_max = max(all_y_values)

    range_width = current_max - current_min
    padding = max(0.05, range_width * 0.15)

    y_limit_low = max(0, current_min - padding)
    y_limit_high = min(1.05, current_max + padding)

    # Plotting
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(14, 7))

    ax = sns.lineplot(
        data=bin_analysis,
        x='Bin_Label',
        y='Accuracy',
        marker='o',
        color='royalblue',
        linewidth=2.5,
        label='Accuracy per Bin'
    )

    # Add average line
    plt.axhline(overall_acc, color='red', linestyle='--', label=f'Global Average ({overall_acc:.2%})')

    # labels/formatting
    plt.title(f"Model Performance vs. {feature_col}", fontsize=14)
    plt.xlabel(f"Binned Range of {feature_col}", fontsize=12)
    plt.ylabel("Accuracy Score", fontsize=12)
    plt.xticks(rotation=45, ha='right')

    plt.ylim(y_limit_low, y_limit_high)

    plt.legend(loc='lower left')

    # label bins with sample sizes
    for i, row in bin_analysis.iterrows():
        if row['Sample_Count'] > 0:
            ax.text(i, row['Accuracy'] + (padding * 0.1), f"n={int(row['Sample_Count'])}",
                    ha='center', fontsize=8, color='black')

    # Save figure
    plt.tight_layout()
    plt.savefig(f"analysis_{feature_col}.png")
    plt.show()

def analyze_performance(csvPath, pred_col_name, target_col_name, feature_col_name, results_folder_path, threshold = float(0.5),
                        exclude_top_1p_outliers = True):
    """
    Analyze Features
    """
    # Get file path and load data
    file_path = csvPath.strip()
    try:
        df = pd.read_csv(file_path, low_memory=False)
    except FileNotFoundError:
        print(f"Error: {file_path} not found")
        return

    pred_col = pred_col_name.strip()
    target_col = target_col_name.strip()
    feature_col = feature_col_name.strip()

    # remove nans and ensure numeric features
    df_test = df.dropna(subset=[pred_col]).copy()
    df_test[feature_col] = pd.to_numeric(df_test[feature_col], errors='coerce')
    df_test = df_test.dropna(subset=[feature_col])

    # remove top 1% outliers to improve visualization (optional)
    clip_outliers = exclude_top_1p_outliers
    if clip_outliers:
        upper_limit = df_test[feature_col].quantile(0.99)
        df_test = df_test[df_test[feature_col] <= upper_limit]

    # Calculate binary predictions and correctness
    df_test['Prediction'] = (df_test[pred_col] >= threshold).astype(int)
    df_test['Is_Correct'] = (df_test['Prediction'] == df_test[target_col]).astype(int)

    # Bin the feature values into intervals
    num_bins = 15
    f_min, f_max = df_test[feature_col].min(), df_test[feature_col].max()
    bins = np.linspace(f_min, f_max, num_bins + 1)
    df_test['Bin_Interval'] = pd.cut(df_test[feature_col], bins=bins, include_lowest=True)

    # Group by bins and calculate accuracy and sample counts
    bin_analysis = df_test.groupby('Bin_Interval', observed=True)['Is_Correct'].agg(['mean', 'count']).reset_index()
    bin_analysis.columns = ['Interval', 'Accuracy', 'Sample_Count']

    # Helper function to format axis labels based on data scale/type
    def format_bin_label(interval):
        left, right = interval.left, interval.right
        if f_min >= 0 and left < 0: left = 0
        use_sci = (abs(right) < 0.01 and right != 0)
        is_int = np.issubdtype(df_test[feature_col].dtype, np.integer) or all(df_test[feature_col] % 1 == 0)
        if use_sci:
            return f"{left:.2e} to {right:.2e}"
        elif is_int:
            return f"{int(round(left))} to {int(round(right))}"
        else:
            return f"{left:.4f} to {right:.4f}"

    bin_analysis['Bin_Label'] = bin_analysis['Interval'].apply(format_bin_label)

    # Dynamic Y
    y_min_data = bin_analysis['Accuracy'].min()
    y_max_data = bin_analysis['Accuracy'].max()
    overall_acc = df_test['Is_Correct'].mean()

    all_y_values = [y_min_data, y_max_data, overall_acc]
    current_min = min(all_y_values)
    current_max = max(all_y_values)

    range_width = current_max - current_min
    padding = max(0.05, range_width * 0.15)

    y_limit_low = max(0, current_min - padding)
    y_limit_high = min(1 + padding, current_max + padding)

    # Plotting
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(14, 7))

    ax = sns.lineplot(
        data=bin_analysis,
        x='Bin_Label',
        y='Accuracy',
        marker='o',
        color='royalblue',
        linewidth=2.5,
        label='Accuracy per Bin'
    )

    # Add average line
    plt.axhline(overall_acc, color='red', linestyle='--', label=f'Global Average ({overall_acc:.2%})')

    # labels/formatting
    plt.title(f"Model Performance vs. {feature_col}", fontsize=14)
    plt.xlabel(f"Binned Range of {feature_col}", fontsize=12)
    plt.ylabel("Accuracy Score", fontsize=12)
    plt.xticks(rotation=45, ha='right')

    plt.ylim(y_limit_low, y_limit_high)

    plt.legend(loc='lower left')

    # label bins with sample sizes
    for i, row in bin_analysis.iterrows():
        if row['Sample_Count'] > 0:
            ax.text(i, row['Accuracy'] + (padding * 0.1), f"n={int(row['Sample_Count'])}",
                    ha='center', fontsize=8, color='black')

    # Save figure
    plt.tight_layout()
    plt.savefig(os.path.join(results_folder_path, f"analysis_{feature_col}.png"))


if __name__ == "__main__":
    analyze_performance_by_feature()