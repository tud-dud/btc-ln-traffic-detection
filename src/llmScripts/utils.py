from tabnanny import verbose

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_auc_score, RocCurveDisplay
from sklearn.inspection import permutation_importance

# Helper Functions for LM Scripts

def load_dataset(path):
    """
    Load dataset from csv file
    """
    if path.endswith('.csv'):
        return pd.read_csv(path)
    else:
        raise ValueError("Unsupported file format. Please provide a .csv file.")


def get_column_selection(df):
    """
    Get column selection for Features and Targets
    """
    print("\nPreview 5 Rows")
    print(df.head())
    print("\nAvailable Columns:")
    for i, col in enumerate(df.columns):
        print(f"[{i}] {col}")

    print("\nSelect Feature Columns:")
    feat_input = input("Enter indices (a-b): ").strip().lower()

    target_idx = int(input("\nEnter the index of the Target Column: "))
    target_name = df.columns[target_idx]

    indices = []
    for part in feat_input.split(','):
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            indices.extend(range(start, end + 1))
        else:
            indices.append(int(part))

    X = df.iloc[:, indices]
    y = df.iloc[:, target_idx]

    print("\nPREVIEW")
    print(f"Selected Target: '{target_name}'")
    print(y.head())
    print(f"\nSelected Features, Shape: {X.shape}")
    print(X.head())

    return X, y, target_name

def get_column_selection_with_inputs(df, feat_input_start_col, feat_input_end_col, target_idx):
    """
    Get column selection for Features and Targets with specific inputs
    """

    target_idx = int(target_idx)
    target_name = df.columns[target_idx]

    indices = []
    indices.extend(range(feat_input_start_col, feat_input_end_col + 1))


    X = df.iloc[:, indices]
    y = df.iloc[:, target_idx]

    print("\nPREVIEW")
    print(f"Selected Target: '{target_name}'")
    print(y.head())
    print(f"\nSelected Features, Shape: {X.shape}")
    print(X.head())

    return X, y, target_name


def calculate_permutation_importance(model, X_test, y_test, feature_names, max_samples = 5000, n_repeats=10):
    """
    Calculate Permutation Importance of a model
    """
    if len(X_test) > max_samples:
        print(f"Selecting {max_samples} samples, because {len(X_test)} samples are too large.")
        X_sub = X_test.sample(n=max_samples, random_state=187)
        y_sub = y_test.loc[X_sub.index]
    else:
        X_sub = X_test
        y_sub = y_test

    # permutation importance with n_repeats
    result = permutation_importance(
        model, X_sub, y_sub, n_repeats=n_repeats, random_state=187, scoring='roc_auc'
    )

    # Create Dataframe with Importance Feature Importances
    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': result.importances_mean,
        'Std': result.importances_std
    }).sort_values(by='Importance', ascending=False)

    return importance_df