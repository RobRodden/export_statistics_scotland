import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# 1. Setup Paths
root_dir = Path(__file__).parent.parent
raw_data_path = root_dir / "data" / "raw" / "ESS+2023+-+Published+Tables.xlsx"
processed_dir = root_dir / "data" / "processed"
output_path = processed_dir / "clean_ESS_data.json"

processed_dir.mkdir(parents=True, exist_ok=True)
print("Reading Excel file... (Heavy lifting in progress)")

# 2. Ingest & Clean Metadata
metadata_df = pd.read_excel(raw_data_path, sheet_name="Table 1 Exports by destination", nrows=3, usecols="A", header=None)
raw_notes = metadata_df[0].astype(str).str.strip().tolist()
excel_notes = "\n".join([line for line in raw_notes if line.lower() != "nan"])

exclude_list = ["Table 1: ", "This worksheet contains one table.", "(£ million)"]
for word in exclude_list:
    excel_notes = excel_notes.replace(word, "")
excel_notes = "\n".join([line.strip() for line in excel_notes.splitlines() if line.strip()])

# 3. Ingest Main Data
excel_data = pd.read_excel(raw_data_path, sheet_name="Table 1 Exports by destination", header=4, usecols="A:Q").dropna(how="all")
excel_data["Destination"] = excel_data["Destination"].astype(str).str.strip()
years = [col for col in excel_data.columns if col != "Destination"]

for col in years:
    excel_data[col] = pd.to_numeric(excel_data[col].astype(str).str.replace(',', ''), errors='coerce') / 1000

def get_series(name):
    return excel_data[excel_data["Destination"] == name][years].values.flatten().tolist()

ruk = get_series("Total RUK Exports")
eu = get_series("Total EU Exports")
intl_total = get_series("Total International Exports") # Fixed typo in string
grand_total = get_series("Total RUK + International Exports")

# 4. Feature Engineering
non_eu = [intl - e for intl, e in zip(intl_total, eu)]

# 5. Build Final JSON
json_payload = {
    "metadata": {
        "last_updated": datetime.now().strftime("%d %B %Y"), # Fixed: was a '.' now a ','
        "notes": excel_notes,
        "source": "Export Statistics Scotland (ESS) 2023"
    },
    "years": [int(y) for y in years],
    "data": {
        "ruk": ruk,
        "eu": eu,
        "non_eu": non_eu,
        "total": grand_total
    }
}

with open(output_path, "w") as f:
    json.dump(json_payload, f, indent=4)

print(f"Successfully created: {output_path.name} in {processed_dir}")