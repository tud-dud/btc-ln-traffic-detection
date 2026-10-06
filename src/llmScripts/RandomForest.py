import os.path

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from llmScripts.utils import *

def main():
    train_path = input("Enter path to your train data file: ").strip()
    # read data
    df_raw = load_dataset(train_path)

    X, y, target_name = get_column_selection(df_raw)

    if (input("Split for eval.? y/n: ") == "y"):
        test_size_val = input("\nEnter test size (default 0.2 = 20%): ").strip()
        test_size = float(test_size_val) if test_size_val else 0.2

        # Split rows for Train Test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=187,
            stratify=y
        )
        df_raw_test = df_raw
    else:
        X_train, y_train = X, y
        test_path = input("Enter path to your test data file: ").strip()
        df_raw_test = load_dataset(test_path)
        # read test dataset
        X_test, y_test, target_name2 = get_column_selection(df_raw_test)

        if not all(col in X_test.columns for col in X_train.columns):
            missing = set(X_train.columns) - set(X_test.columns)
            print(f"Error: Test set is missing columns: {missing}")
            exit(1)
        # Same Order
        X_test = X_test[X_train.columns]

        if (target_name != target_name2):
            print(f"Warning: Target names differ ({target_name} vs {target_name2})")

    # create rf classifier
    classifier = RandomForestClassifier(
        n_estimators=100,
        random_state=187,
        n_jobs=-1  # all cores
    )

    # Fit classifier
    print("Fitting model")
    classifier.fit(X_train, y_train.values.ravel())

    # Predict Test dataset
    print("Predicting probabilities")
    y_probs = classifier.predict_proba(X_test)[:, 1]

    # Calc feature importance
    print("Calculating Feature Importance (Permutation)")
    importance_df = calculate_permutation_importance(classifier, X_test, y_test, X_test.columns)

    # Create Output Dataframe with predictions and save to csv
    output_df = df_raw_test.copy()
    output_df['RF Prediction Prob'] = np.nan
    output_df.loc[X_test.index, 'RF Prediction Prob'] = y_probs
    output_df.to_csv("rf_predictions.csv", index=True)

    print(f"\nResults Saved: rf_predictions.csv")
    auc_score = round(roc_auc_score(y_test, y_probs), 4)
    print(f"Random Forest AUC: {auc_score}")

    sns.set_theme(style="whitegrid")

    # Plot AUC-ROC
    plt.figure(figsize=(8, 6))
    RocCurveDisplay.from_predictions(y_test, y_probs, name="Random Forest", color="darkgreen")
    plt.title(f"Random Forest ROC Curve")
    plt.legend([f"Random Forest (AUC = {auc_score})"], loc="lower right", fontsize=10)
    plt.savefig("rf_auc_curve.png")

    # Plot Distribution
    plt.figure(figsize=(10, 6))
    plot_df = pd.DataFrame({'Prob': y_probs, 'Target': y_test.values.ravel()})
    sns.kdeplot(data=plot_df, x='Prob', hue='Target', fill=True, common_norm=False, palette="mako")
    plt.title("RF Probability Distribution (Test Set)")
    plt.savefig("rf_prob_distribution.png")

    # Plot Feature Importance
    plt.figure(figsize=(10, 8))
    sns.barplot(
        data=importance_df,
        x='Importance',
        y='Feature',
        hue='Feature',
        palette="viridis",
        legend=False
    )
    plt.title("Feature Importance (Permutation on Test Set)")
    plt.xlabel("Decrease in ROC-AUC Score")
    plt.tight_layout()
    plt.savefig("rf_feature_importance.png")

    print("Plots saved")
    print("\nImportant Features:")
    print(importance_df)


def run_random_forrest(train_path, results_path, feat_input_start_col, feat_input_end_col, target_idx, test_size_val=0.2):
    # read data
    df_raw = load_dataset(train_path)

    X, y, target_name = get_column_selection_with_inputs(df_raw, feat_input_start_col, feat_input_end_col, target_idx)

    test_size = float(test_size_val)

    # Split rows for Train Test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=187,
        stratify=y
    )
    df_raw_test = df_raw

    # create rf classifier
    classifier = RandomForestClassifier(
        n_estimators=100,
        random_state=187,
        n_jobs=-1  # all cores
    )

    # Fit classifier
    print("Fitting model")
    classifier.fit(X_train, y_train.values.ravel())

    # Predict Test dataset
    print("Predicting probabilities")
    y_probs = classifier.predict_proba(X_test)[:, 1]

    # Calc feature importance
    print("Calculating Feature Importance (Permutation)")
    importance_df = calculate_permutation_importance(classifier, X_test, y_test, X_test.columns)

    # Create Output Dataframe with predictions and save to csv
    output_df = df_raw_test.copy()
    output_df['RF Prediction Prob'] = np.nan
    output_df.loc[X_test.index, 'RF Prediction Prob'] = y_probs
    output_df.to_csv(os.path.join(results_path, "rf_predictions.csv"), index=True)

    print(f"\nResults Saved: rf_predictions.csv")
    auc_score = round(roc_auc_score(y_test, y_probs), 4)
    print(f"Random Forest AUC: {auc_score}")

    sns.set_theme(style="whitegrid")

    # Plot AUC-ROC
    plt.figure(figsize=(8, 6))
    RocCurveDisplay.from_predictions(y_test, y_probs, name="Random Forest", color="darkgreen")
    plt.title(f"Random Forest ROC Curve")
    plt.legend([f"Random Forest (AUC = {auc_score})"], loc="lower right", fontsize=10)
    plt.savefig(os.path.join(results_path, "rf_auc_curve.png"))

    # Plot Distribution
    plt.figure(figsize=(10, 6))
    plot_df = pd.DataFrame({'Prob': y_probs, 'Target': y_test.values.ravel()})
    sns.kdeplot(data=plot_df, x='Prob', hue='Target', fill=True, common_norm=False, palette="mako", clip=(0, 1))
    plt.title("RF Probability Distribution (Test Set)")
    plt.savefig(os.path.join(results_path, "rf_prob_distribution.png"))

    # Plot Feature Importance
    plt.figure(figsize=(10, 8))
    sns.barplot(
        data=importance_df,
        x='Importance',
        y='Feature',
        hue='Feature',
        palette="viridis",
        legend=False
    )
    plt.title("Feature Importance (Permutation on Test Set)")
    plt.xlabel("Decrease in ROC-AUC Score")
    plt.tight_layout()
    plt.savefig(os.path.join(results_path, "rf_feature_importance.png"))

    print("Plots saved")
    print("\nImportant Features:")
    print(importance_df)


if __name__ == "__main__":
    main()