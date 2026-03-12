import pandas as pd
from pathlib import Path

# 1. Setup Paths
root_dir = Path(__file__).parent.parent
raw_data_path = root_dir / "data" / "raw" / "ESS+2023+-+Published+Tables.xlsx"
processed_dir = root_dir / "data" / "processed"
output_path = processed_dir / "clean_ESS_data.csv"
notes_path = processed_dir / "metadata_notes.txt"

# Ensure output directory exists
processed_dir.mkdir(parents=True, exist_ok=True)
print("Reading Excel file... (this is the slow part we are skipping for users)")

# 2. Ingest Data
# Extract Metadata Notes (The part we missed before)
metadata_df = pd.read_excel(raw_data_path, sheet_name="Table 1 Exports by destination", nrows=3, usecols="A", header=None)

# Convert to list, strip spaces, and REMOVE 'nan' values (important!)
raw_notes = metadata_df[0].astype(str).str.strip().tolist()
excel_notes = "\n".join([line for line in raw_notes if line.lower() != "nan"])

# Clean up specific phrases
exclude_list = ["Table 1: ", "This worksheet contains one table."]
for word in exclude_list:
    excel_notes = excel_notes.replace(word, "")

# Final sweep: remove any leftover empty lines or leading/trailing whitespace
excel_notes = "\n".join([line.strip() for line in excel_notes.splitlines() if line.strip()])

# Write to file
with open(notes_path, "w") as f:
    f.write(excel_notes)

# OLD
# metadata_df = pd.read_excel(raw_data_path, sheet_name="Table 1 Exports by destination", nrows=3, usecols="A", header=None)
# # excel_notes = "\n".join(metadata_df[0].astype(str).str.strip().tolist()) # REPLACE?
# excel_notes_imported = "\n".join(metadata_df[0].astype(str).str.strip().tolist())

# excel_note = excel_notes_imported
# exclude_list = ["Table 1: ", "This worksheet contains one table."]

# for word in exclude_list:
#     excel_note = excel_note.replace(word, "")
# excel_note = "\n".join([line.strip() for line in excel_note.splitlines() if line.strip()])

# with open(notes_path, "w") as f:
#     f.write(excel_note)

# ------- THIS NEEDS TO BE INCORPORATED -------
# 1.2 Report Metadata Extraction (Dynamic)


       # 5.7 Metadata Cleaning Loop

        # excel_notes = excel_notes_imported
        # exclude_list = ["Table 1: ", "This worksheet contains one table."]
        # for word in exclude_list:
        #     excel_notes = excel_notes.replace(word, "")

        # excel_notes = "\n".join([line.strip() for line in excel_notes.splitlines() if line.strip()])
# -----------------------------------------------

# 2. Ingest Data (The main data we will use for the app)
excel_data = pd.read_excel(raw_data_path, sheet_name="Table 1 Exports by destination", header=4, usecols="A:Q").dropna(how="all")

# 3. Clean & Standardise
excel_data["Destination"] = excel_data["Destination"].astype(str).str.strip() # Remove leading/trailing spaces
years = [col for col in excel_data.columns if col != "Destination"] # Get year columns

for col in years:
    excel_data[col] = pd.to_numeric(excel_data[col].astype(str).str.replace(',', ''), errors='coerce')

# 4. Feature Engineering: Create 'International Non-EU'
new_row = {"Destination": "International Non-EU"}
for year in years:
    intl_val = excel_data.loc[excel_data["Destination"] == "Total International Exports", year].sum()
    eu_val = excel_data.loc[excel_data["Destination"] == "Total EU Exports", year].sum()
    new_row[year] = intl_val - eu_val

excel_data = pd.concat([excel_data, pd.DataFrame([new_row])], ignore_index=True)

# 5. transform from wide to long format
summary_categories = ["Total RUK Exports", "Total EU Exports", "International Non-EU", "Total RUK + International Exports"]
data_final = excel_data[excel_data["Destination"].isin(summary_categories)].copy()

# Melt into a tidy format: Year, Destination, Export_Value
data_final = data_final.melt(id_vars=["Destination"], var_name="Year", value_name="Export_Value")
data_final["Export_Value"] = data_final["Export_Value"] / 1000 # Convert to Billions
data_final["Year"] = data_final["Year"].astype(int)

# 6. Save the result
#output_name = f"{sheet_name.replace(' ', '_')}.csv"
data_final.to_csv(output_path, index=False)
print(f"Successfully created: {output_path.name} and {notes_path.name} in {processed_dir}  folder.")

print("\n--- All done! Check your folder. ---")

# for sheet_name, df in excel_data.items():


#     if sheet_name == specific_sheet_name:
#         # 1. Slice rows AND columns (Columns 0 to 16 are Destination + Years 2008-2023)
#         # This effectively stops at Column O
#         df = df.iloc[4:, :17].reset_index(drop=True)
        
#         # 2. Define Year list to avoid typing them 100 times
#         years = [str(year) for year in range(2008, 2024)]
#         df.columns = ['Destination'] + years

#         # --- ADD THIS LINE HERE ---
#         # This removes leading/trailing spaces from every name in that column
#         df['Destination'] = df['Destination'].str.strip()

#         # Clean the numbers (remove commas/spaces and convert to float)
#         for col in years:
#             df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

#         # 4. MATH: Create 'International Non-EU' using a loop
#         # This is much safer than manual variables!
#         new_row_data = {'Destination': 'International Non-EU'}
        
#         for year in years:
#             # Get the values for this specific year
#             intl_val = df.loc[df['Destination'] == 'Total International Exports', year].values[0]
#             eu_val = df.loc[df['Destination'] == 'Total EU Exports', year].values[0]
#             # Save the result into our dictionary
#             new_row_data[year] = intl_val - eu_val

#         # 5. Add new row
#         df = pd.concat([df, pd.DataFrame([new_row_data])], ignore_index=True)
        
#         # --- NEW STEP: Remove the redundant rows ---
#         # We remove the "Totals" that would cause double-counting in a chart
#         rows_to_remove = ['Total International Exports', 'Total RUK + International Exports']
#         df = df[~df['Destination'].isin(rows_to_remove)]
        
#         # 6. The Melt (id_vars uses a list [])
#         df = df.melt(id_vars=['Destination'], var_name='Year', value_name='Export_Value')