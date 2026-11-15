"""
Weather Data Analyzer
====================
PS No.: 94
Project Title: Weather Data Analyzer
Problem Statement:
Build a program that loads daily weather data (date, temperature, humidity, rainfall)
from a CSV file, cleans it, and analyses it to find hottest/coldest days, averages
and rainfall trends, with charts.

Language: Python 3
Concepts: Pandas, NumPy, Matplotlib, Data Cleaning
CSV Columns: Date, Temp, Humidity, Rainfall
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt


def format_num(val):
    """Format float number as integer if it represents a whole number, else 2 decimal places."""
    try:
        val_float = float(val)
        if val_float.is_integer():
            return str(int(val_float))
        return f"{val_float:.2f}"
    except (ValueError, TypeError):
        return str(val)


def load_weather_data(file_path):
    """
    Loads weather data from a CSV file using Pandas.
    Auto-detects header presence and standardizes column names.
    Returns (DataFrame, None) or (None, error_message).
    """
    cleaned_path = file_path.strip().strip("'\"").lstrip("\ufeff")
    if not os.path.exists(cleaned_path):
        return None, f"Error: File '{cleaned_path}' not found. Please enter a valid file name."

    try:
        # Check first line to determine if header exists
        with open(cleaned_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip().lstrip("\ufeff")

        col_names = ["Date", "Temp", "Humidity", "Rainfall"]
        first_cols = [c.strip().lower() for c in first_line.split(",") if c.strip()]

        # Check if first row contains column headers
        has_header = any(keyword in first_cols for keyword in ["date", "temp", "humidity", "rainfall"])

        if has_header:
            df = pd.read_csv(cleaned_path)
            # Normalize column names case-insensitively
            col_map = {}
            for col in df.columns:
                lower = str(col).strip().lower().lstrip("\ufeff")
                if "date" in lower:
                    col_map[col] = "Date"
                elif "temp" in lower:
                    col_map[col] = "Temp"
                elif "hum" in lower:
                    col_map[col] = "Humidity"
                elif "rain" in lower:
                    col_map[col] = "Rainfall"
            df = df.rename(columns=col_map)
        else:
            df = pd.read_csv(cleaned_path, header=None, names=col_names)

        # Ensure required columns exist
        for expected_col in col_names:
            if expected_col not in df.columns:
                df[expected_col] = np.nan

        # Coerce numeric columns
        for num_col in ["Temp", "Humidity", "Rainfall"]:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

        return df, None
    except Exception as e:
        return None, f"Error reading file '{cleaned_path}': {str(e)}"


def generate_summary(df):
    """
    Computes weather statistics using NumPy and returns the formatted summary string.
    - If 1 row:
      Average Temp: XX.XX C | Max: XX | Min: XX | Std Dev: XX.XX
    - If >1 rows:
      Average Temp: XX.XX C | Max: XX (Date) | Min: XX (Date) | Total Rainfall: XX mm
    """
    # Extract temperature and rainfall arrays using NumPy
    temps = df["Temp"].dropna().to_numpy(dtype=float)
    rainfalls = df["Rainfall"].dropna().to_numpy(dtype=float)

    if len(temps) == 0:
        return "No valid temperature data available."

    # NumPy statistical calculations
    avg_temp = float(np.mean(temps))
    max_temp = float(np.max(temps))
    min_temp = float(np.min(temps))
    std_dev = float(np.std(temps))
    total_rain = float(np.sum(rainfalls)) if len(rainfalls) > 0 else 0.0

    if len(df) == 1:
        # Boundary / Minimum Input (1 row only)
        return (
            f"Average Temp: {avg_temp:.2f} C | "
            f"Max: {format_num(max_temp)} | "
            f"Min: {format_num(min_temp)} | "
            f"Std Dev: {std_dev:.2f}"
        )
    else:
        # Normal Input (>1 rows)
        # Find dates of max and min temperature
        max_mask = df["Temp"] == max_temp
        min_mask = df["Temp"] == min_temp

        max_date = str(df.loc[max_mask, "Date"].iloc[0]) if max_mask.any() else "N/A"
        min_date = str(df.loc[min_mask, "Date"].iloc[0]) if min_mask.any() else "N/A"

        return (
            f"Average Temp: {avg_temp:.2f} C | "
            f"Max: {format_num(max_temp)} ({max_date}) | "
            f"Min: {format_num(min_temp)} ({min_date}) | "
            f"Total Rainfall: {format_num(total_rain)} mm"
        )


def clean_and_plot(df, output_dir=None, show_charts=True):
    """
    Cleans data (removes duplicates, fills missing Temp with mean)
    and plots Matplotlib charts (Line chart for Temp trend, Bar chart for Rainfall).
    Returns (cleaned_df, status_lines).
    """
    status_lines = []

    # 1. Handle Duplicates
    duplicates_removed = int(df.duplicated().sum())
    cleaned_df = df.drop_duplicates().reset_index(drop=True)

    # 2. Handle Missing Values
    missing_temp_count = int(cleaned_df["Temp"].isna().sum())
    valid_temps = cleaned_df["Temp"].dropna().to_numpy(dtype=float)

    if len(valid_temps) > 0:
        temp_mean = float(np.mean(valid_temps))
    else:
        temp_mean = 0.0

    if missing_temp_count > 0:
        cleaned_df["Temp"] = cleaned_df["Temp"].fillna(temp_mean)
        status_lines.append(
            f"Duplicates removed: {duplicates_removed} | Missing Temp filled with mean: {temp_mean:.2f}"
        )
    else:
        status_lines.append(
            f"Duplicates removed: {duplicates_removed} | Missing Temp filled with mean: {temp_mean:.2f}"
        )

    # Fill any remaining NaNs in other columns cleanly
    if cleaned_df["Humidity"].isna().any():
        med_hum = float(np.nanmedian(cleaned_df["Humidity"].to_numpy()))
        cleaned_df["Humidity"] = cleaned_df["Humidity"].fillna(med_hum)

    if cleaned_df["Rainfall"].isna().any():
        cleaned_df["Rainfall"] = cleaned_df["Rainfall"].fillna(0.0)

    # 3. Status Line for Cleaned Rows & Chart
    status_lines.append(
        f"Cleaned rows: {len(cleaned_df)} | Line chart 'Temperature Trend' displayed"
    )

    # 4. Matplotlib Visualizations (Line and Bar)
    target_dir = output_dir if output_dir else os.path.dirname(os.path.abspath(__file__))

    # Separate Chart 1: Line Chart - Temperature Trend
    fig1, ax1 = plt.subplots(figsize=(8, 4.5))
    dates = [str(d) for d in cleaned_df["Date"]]
    ax1.plot(dates, cleaned_df["Temp"], marker="o", color="#e74c3c", linewidth=2.5, markersize=8)
    ax1.set_title("Temperature Trend", fontsize=14, fontweight="bold", pad=12)
    ax1.set_xlabel("Date", fontsize=11, labelpad=8)
    ax1.set_ylabel("Temperature (°C)", fontsize=11, labelpad=8)
    ax1.grid(True, linestyle="--", alpha=0.6)
    for i, txt in enumerate(cleaned_df["Temp"]):
        ax1.annotate(f"{txt:.1f}°C", (dates[i], cleaned_df["Temp"][i]),
                     textcoords="offset points", xytext=(0, 10), ha="center", fontsize=9)
    plt.tight_layout()
    line_chart_path = os.path.join(target_dir, "temperature_trend.png")
    fig1.savefig(line_chart_path, dpi=150)
    plt.close(fig1)

    # Separate Chart 2: Bar Chart - Daily Rainfall Trend
    fig2, ax2 = plt.subplots(figsize=(8, 4.5))
    ax2.bar(dates, cleaned_df["Rainfall"], color="#3498db", edgecolor="#2980b9", width=0.45)
    ax2.set_title("Daily Rainfall Trend", fontsize=14, fontweight="bold", pad=12)
    ax2.set_xlabel("Date", fontsize=11, labelpad=8)
    ax2.set_ylabel("Rainfall (mm)", fontsize=11, labelpad=8)
    ax2.grid(True, linestyle="--", alpha=0.6, axis="y")
    for i, txt in enumerate(cleaned_df["Rainfall"]):
        ax2.annotate(f"{txt:.1f}mm", (dates[i], cleaned_df["Rainfall"][i]),
                     textcoords="offset points", xytext=(0, 6), ha="center", fontsize=9)
    plt.tight_layout()
    bar_chart_path = os.path.join(target_dir, "rainfall_trend.png")
    fig2.savefig(bar_chart_path, dpi=150)

    if show_charts:
        try:
            if matplotlib.get_backend().lower() not in ["agg", "pdf", "ps", "svg"]:
                plt.show(block=False)
                plt.pause(1.0)
        except Exception:
            pass
    plt.close(fig2)

    return cleaned_df, status_lines


def show_pandas_summary(df):
    """Requirement 2: Load the CSV file using Pandas and show a short data summary."""
    print("\n--- Short Data Summary (Pandas) ---")
    print(f"Total Rows: {len(df)} | Columns: {list(df.columns)}")
    print(df.to_string(index=False))
    print("----------------------------------\n")


def prompt_for_file(allow_cancel=False):
    """
    Prompts the user to enter a CSV file name until valid or cancelled.
    Returns (DataFrame, filename) or (None, None).
    """
    prompt_msg = "Enter CSV file name (or type 'cancel' to go back): " if allow_cancel else "Enter CSV file name: "
    while True:
        try:
            raw_input = input(prompt_msg)
            filename = raw_input.strip().lstrip("\ufeff")
        except (EOFError, KeyboardInterrupt):
            return None, None

        if allow_cancel and filename.lower() in ["cancel", "back", "b"]:
            return None, None

        if not filename:
            print("File name cannot be empty. Please enter a valid file name.")
            continue

        df, err = load_weather_data(filename)
        if err:
            print(err)
            continue
        return df, filename


def run_interactive():
    """Runs interactive console loop for the Weather Data Analyzer."""
    print("========================================")
    print("      Weather Data Analyzer (PS 94)     ")
    print("========================================")

    df, current_file = prompt_for_file(allow_cancel=False)
    if df is None:
        print("\nExiting program.")
        return

    # Show short data summary using Pandas
    show_pandas_summary(df)

    # Interactive Menu Loop
    while True:
        print(f"\n[Active File: {current_file}]")
        print("Select Menu Option:")
        print("1. Summary")
        print("2. Clean & Plot")
        print("3. Change CSV File")
        print("4. Exit")
        try:
            choice = input("Enter choice (1-4): ").strip().lstrip("\ufeff").lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if choice in ["1", "summary"]:
            # Menu Option 1: Summary
            summary_output = generate_summary(df)
            print(summary_output)
        elif choice in ["2", "clean", "clean & plot", "plot"]:
            # Menu Option 2: Clean & Plot
            cleaned_df, status_lines = clean_and_plot(df, show_charts=True)
            for line in status_lines:
                print(line)
            # Update working df to cleaned version
            df = cleaned_df
        elif choice in ["3", "change", "change file", "load", "switch"]:
            # Menu Option 3: Change CSV File
            print("\n--- Change CSV File ---")
            new_df, new_file = prompt_for_file(allow_cancel=True)
            if new_df is not None:
                df = new_df
                current_file = new_file
                print(f"\n[OK] Switched to '{current_file}' successfully!")
                show_pandas_summary(df)
            else:
                print(f"Keeping current active file: '{current_file}'")
        elif choice in ["4", "exit", "quit", "q"]:
            print("Exiting Weather Data Analyzer.")
            break
        else:
            print("Invalid option. Please enter 1, 2, 3, or 4.")


def main():
    """Main CLI entrypoint supporting both command-line arguments and interactive mode."""
    args = sys.argv[1:]

    if not args:
        run_interactive()
        return

    # CLI Argument mode (useful for grading scripts, batch runs, automated testing)
    # Usage: python weather_analyzer.py <filename> [option: 1 or 2]
    filename = args[0]
    option = args[1] if len(args) > 1 else None

    df, err = load_weather_data(filename)
    if err:
        print(err)
        sys.exit(1)

    if option == "1":
        print(generate_summary(df))
    elif option == "2":
        _, status_lines = clean_and_plot(df, show_charts=False)
        for line in status_lines:
            print(line)
    else:
        # If no option specified, execute both summary and clean & plot
        show_pandas_summary(df)
        print(generate_summary(df))
        _, status_lines = clean_and_plot(df, show_charts=False)
        for line in status_lines:
            print(line)


if __name__ == "__main__":
    main()
