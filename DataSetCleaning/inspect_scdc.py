import pandas as pd
import os


FOLDER_PATH = "//"

files = [
    "SCDC_Tracker_2020.xlsx",
    "SCDC_Tracker_2021.xlsx",
    "SCDC_Tracker_2022.xlsx",
    "SCDC_Tracker_2023.xlsx",
    "SCDC_Tracker_2024.xlsx"
]


for file in files:

    path = os.path.join(FOLDER_PATH, file)

    print()
    print("=" * 70)
    print(file)
    print("=" * 70)

    excel = pd.ExcelFile(path)

    print("Sheets:")
    print(excel.sheet_names)

    for sheet in excel.sheet_names:

        df = pd.read_excel(
            path,
            sheet_name=sheet
        )

        print()
        print("--- Sheet:", sheet, "---")
        print("Rows:", len(df))
        print("Columns:")
        print(list(df.columns))