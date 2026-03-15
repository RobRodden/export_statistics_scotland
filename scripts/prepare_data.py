import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# 1. Setup Paths
root_dir = Path(__file__).parent.parent
raw_data_path = root_dir / "data_raw"
processed_dir = root_dir / "app" / "data_processed"

# Specific file paths
# Path to excel file
excel_path = raw_data_path / "ESS+2023+-+Published+Tables.xlsx"

# Path to csv file
csv_path = raw_data_path / "updated_ess_2023_data_rebased_2008_2023.csv"

# Define output path
output_path = processed_dir / "clean_ESS_data.json"

processed_dir.mkdir(parents=True, exist_ok=True)
print("Reading Excel file... (Heavy lifting in progress)")

# 2. Ingest & Clean ESS metadata
metadata_df = pd.read_excel(excel_path, sheet_name="Table 1 Exports by destination", nrows=3, usecols="A", header=None)
raw_notes = metadata_df[0].astype(str).str.strip().tolist()
excel_notes = "\n".join([line for line in raw_notes if line.lower() != "nan"])

exclude_list = ["Table 1: ", "This worksheet contains one table.", "(£ million)"]
for word in exclude_list:
    excel_notes = excel_notes.replace(word, "")
excel_notes = "\n".join([line.strip() for line in excel_notes.splitlines() if line.strip()])

# 3. Ingest relevant ESS data
excel_data = pd.read_excel(excel_path, sheet_name="Table 1 Exports by destination", header=4, usecols="A:Q").dropna(how="all")
excel_data["Destination"] = excel_data["Destination"].astype(str).str.strip()
years = [col for col in excel_data.columns if col != "Destination"]

for col in years:
    excel_data[col] = pd.to_numeric(excel_data[col].astype(str).str.replace(',', ''), errors='coerce') / 1000

def get_series(name):
    return excel_data[excel_data["Destination"] == name][years].values.flatten().tolist()

current_ruk = get_series("Total RUK Exports")
current_eu = get_series("Total EU Exports")
current_intl_total = get_series("Total International Exports") # Fixed typo in string
current_grand_total = get_series("Total RUK + International Exports")

# Ingest Additional Information
# Read only the first row to get the column names
temp_df = pd.read_csv(csv_path, nrows=0).dropna(how="all")
actual_columns = temp_df.columns.tolist()

# Find the 'year' column regardless of case (Year, year, YEAR)
year_col_name = next((c for c in actual_columns if c.lower() == "year"), None)

if not year_col_name:
    raise ValueError(f"Could not find a 'year' column in {csv_path.name}. Found: {actual_columns}")

# Find the 'Real' columns
all_real_cols = [c for c in actual_columns if c.endswith("(Real)")]

# safety 
matched_cols = [c for c in all_real_cols if "Non-EU" not in c]

cols_to_import = [year_col_name] + matched_cols

# Now read the actual data
df_real = pd.read_csv(csv_path, usecols=cols_to_import)

# Rename the year column to lowercase 'year' internally for consistency
df_real = df_real.rename(columns={year_col_name: "year"})

# Drop rows where 'year' is empty before converting to int
df_real = df_real.dropna(subset=['year'])

# Force 'year' to be a clean integer (removes decimals like 2008.0)
df_real['year'] = df_real['year'].astype(int)

# Filter to match your Excel years (2008-2023)
# This ensures you don't ingest extra years if the CSV has more data than the Excel
valid_years = [int(y) for y in years]
df_real = df_real[df_real['year'].isin(valid_years)]

# Convert all 'Real' columns to numeric, stripping commas just in case
for col in matched_cols:
    df_real[col] = pd.to_numeric(df_real[col].astype(str).str.replace(',', ''), errors='coerce')
df_real = df_real.sort_values("year")


# Extract lists
real_ruk = df_real["RUK (Real)"].tolist()
real_eu = df_real["EU (Real)"].tolist()
#real_non_eu = df_real["Non-EU (Real)"].tolist()
real_total = df_real["Total (Real)"].tolist()

# 4. Feature Engineering
# Calculate Non-EU
non_eu = [intl - e for intl, e in zip(current_intl_total, current_eu)]

# If your CSV doesn't have non-EU, or you want to be safe:
real_non_eu = [(t - r) - e for t, r, e in zip(real_total, real_ruk, real_eu)]

# 5. Build Final JSON
json_payload = {
    "metadata": {
        "last_updated": datetime.now().strftime("%d %B %Y"), # Fixed: was a '.' now a ','
        "notes": excel_notes,
        "source": "Export Statistics Scotland (ESS) 2023"
    },
    "years": [int(y) for y in years],
    "data": {
        "current_value": {
            "ruk": current_ruk,
            "eu": current_eu,
            "non_eu": non_eu,
            "total": current_grand_total
        },
        "real_value": {
            "ruk": real_ruk,
            "eu": real_eu,
            "non_eu": real_non_eu,
            "total": real_total
        }
    }
}


with open(output_path, "w") as f:
    json.dump(json_payload, f, indent=4)

print(f"Successfully created: {output_path.name} in {processed_dir}")