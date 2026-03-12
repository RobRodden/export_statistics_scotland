import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import io
from shiny import App, render, ui
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------
# 1. PATH & DATA INGESTION
# ---------------------------------------------------------
# 1.1 Relative Pathing (Necessary for Shinylive/Web)
this_dir = Path(__file__).parent
data_path = this_dir / "ESS+2023+-+Published+Tables.xlsx"

# 1.2 Report Metadata Extraction (Dynamic)
metadata_df = pd.read_excel(data_path, sheet_name="Table 1 Exports by destination", nrows=3, usecols="A", header=None)
excel_notes_imported = "\n".join(metadata_df[0].astype(str).str.strip().tolist())

# 1.3 Main Data Ingestion (Desingated Area with Header Alignment)
df = pd.read_excel(data_path, sheet_name="Table 1 Exports by destination", header=4, usecols="A:Q").dropna(how="all")

# 1.4 Events Library for Chart
EVENTS = {
    (2008, 2009): {"label": "Global Financial Crisis", "color": "#d9d9d9"},
    (2014, 2015): {"label": "IndyRef &\nOil Supply Chain Shock", "color": "#fff9c4"},
    (2016, 2019): {"label": "Brexit Referendum\n& consequent uncertainty", "color": "#d9d9d9"},
    (2020, 2021): {"label": "COVID-19 & New EU\nTrade Rules (TCA)", "color": "#fff9c4"},
    (2022, 2023): {"label": "Ukraine War\nEnergy Shock", "color": "#d9d9d9"}
}

# ---------------------------------------------------------
# 2. DATA CLEANING & TYPE CONVERSION
# ---------------------------------------------------------
# 2.1 Standardise Destination Labels
df["Destination"] = df["Destination"].astype(str).str.strip()

# 2.2 Numerical Conversion & Sanitisation Pipeline
for col in df.columns:
    if col != "Destination":
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.replace(" ", ""), errors="coerce")

df = df[df["Destination"].notna()]
years = [col for col in df.columns if col != "Destination"]

# ---------------------------------------------------------
# 3. FEATURE ENGINEERING & CHART PREPARATION
# ---------------------------------------------------------
# 3.1 Establishing Mutual Exclusivity: 'International Non-EU'
new_row = {"Destination": "International Non-EU"}
for year in years:
    intl = df.loc[df["Destination"] == "Total International Exports", year].sum()
    eu = df.loc[df["Destination"] == "Total EU Exports", year].sum()
    new_row[year] = intl - eu

df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

# 3.2 Extract Totals for Line Graph (Converted to Billions)
total_raw = df[df["Destination"] == "Total RUK + International Exports"].copy()
total_values = total_raw[years].values.flatten().astype(float) / 1000

# 3.3 Wide-to-Long Transformation
summary_categories = ["Total RUK Exports", "Total EU Exports", "International Non-EU"]
df_plot = df[df["Destination"].isin(summary_categories)].copy()
df_plot = df_plot.melt(id_vars="Destination", var_name="Year", value_name="Export_Value")
df_plot["Export_Value"] = df_plot["Export_Value"] / 1000
df_plot["Year"] = df_plot["Year"].astype(int)

# ---------------------------------------------------------
# 4. USER INTERFACE (UI)
# ---------------------------------------------------------
# 4.1 UI Container
app_ui = ui.page_fluid(
    ui.div(
        # 4.1.1 Title & Description
        ui.div(
            ui.h2("Export Statistics Scotland (ESS) 2023 Data"),
            ui.p("An visualisation of Scottish exports\n",
                ui.a("return to project repository on github", href="https://github.com/RobRodden/export_statistics_scotland", target="_blank")),
            style="text-align: center; margin-top: 30px; margin-bottom: 10px; color: #333333;"
        ),

        # 4.2 Main Plot Output
        ui.output_plot("trade_plot", height="750px"),
        
        # 4.3 Export Utility & Layout Optimization
        ui.div(
            ui.download_button("download_pdf", "Download PDF Report"),
            style="display: flex; justify-content: center; padding-left: 60px; margin-top: -10px; padding-bottom: 50px;"
        ),
        style="max-width: 1100px; margin: auto;"
    )
)

# ---------------------------------------------------------
# 5. SERVER LOGIC
# ---------------------------------------------------------
# 5.1 Application Server
def server(input, output, session):

    # 5.2 Shared Figure Creation Function
    def create_figure():
        # Setup aesthetics
        ruk_color, eu_color, non_eu_color = "#4C5B7A", "#2A9D8F", "#8ABF88"
        total_line_color = "#222222"

        sns.set_theme(style="white")
        fig = plt.figure(figsize=(12, 10))
        gs = fig.add_gridspec(2, 1, height_ratios=[7.5, 2.5])
        ax, ax_note = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
        ax_note.axis("off")

        # Pivot data for plotting
        pivot = df_plot.pivot(index="Year", columns="Destination", values="Export_Value")
        years_x = pivot.index.values
        x = np.arange(len(years_x))
        width = 0.25

        # 5.3 Economic Event Positioning ("Staircasing")
        years_list = [int(y) for y in pivot.index.values]
        max_val = max(total_values.max(), pivot.values.max())
        ax.set_ylim(0, max_val * 1.20) 
        y_top = ax.get_ylim()[1]

        prev_x_end, state_index = None, 0
        heights = [0.96, 0.89, 0.82] 

        for (yr_start, yr_end), event in EVENTS.items():
            if yr_start in years_list or yr_end in years_list:
                idx_start = years_list.index(max(yr_start, min(years_list)))
                idx_end = years_list.index(min(yr_end, max(years_list)))
                x_center = (idx_start + idx_end) / 2

                # A. Highlight Band
                ax.axvspan(idx_start - 0.5, idx_end + 0.5, color=event["color"], alpha=0.35, zorder=0)

                # B. Staircase Height Logic
                if prev_x_end is not None and abs(idx_start - prev_x_end) <= 2:
                    state_index = (state_index + 1) % 3
                else:
                    state_index = 0

                label_height = y_top * heights[state_index]

                # C. Event Text
                ax.text(x_center, label_height, event["label"], ha="center", va="top",
                        fontsize=8, color="#808080", style="italic", clip_on=False)

                # D. Vertical "Flagpole" Line
                target_y = total_values[idx_start] if idx_start == idx_end else total_values[idx_start:idx_end + 1].mean()
                ax.vlines(x=x_center, ymin=target_y, ymax=label_height - (y_top * 0.04),
                          color="#666666", linewidth=0.6, zorder=1)

                prev_x_end = idx_end

        # 5.4 Bar & Line Plotting
        b1 = ax.bar(x - width, pivot["Total RUK Exports"], width, label="Rest of the UK", color=ruk_color, alpha=0.65, zorder=2)
        b2 = ax.bar(x, pivot["Total EU Exports"], width, label="EU Exports", color=eu_color, alpha=0.65, zorder=2)
        b3 = ax.bar(x + width, pivot["International Non-EU"], width, label="Non-EU Exports", color=non_eu_color, alpha=0.65, zorder=2)
        
        line = ax.plot(x, total_values, color=total_line_color, marker="o", linewidth=1.5, 
                       markersize=2.3, label="Total Outbound Trade", zorder=5)
        
        # 5.5 Chart Styling
        ax.set_xticks(x)
        ax.set_xticklabels(years_x)
        ax.set_ylabel("Value (£ Billions)", fontsize=11, color='#777777')
        ax.set_title("Destination block: 2008 – 2023", fontsize=18, fontweight="bold", pad=25)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.7, alpha=0.25)
        sns.despine(ax=ax, left=True, bottom=True)
        plt.subplots_adjust(bottom=0.25, top=0.88, left=0.12, right=0.88)

        # 5.6 Legend & Metadata Processing
        handles = [b1, b2, b3, line[0]]
        labels = ["Total Rest of UK Exports", "Total EU Exports", "Total Non-EU Exports", "Total Outbound Exports"]
        ax_note.legend(handles, labels, loc="upper center", ncol=4, frameon=False, fontsize=10)

        current_date = datetime.now().strftime("%d %B %Y")
        data_url = "https://www.gov.scot/publications/exports-statistics-scotland-2023/"
        
        # 5.7 Metadata Cleaning Loop
        excel_notes = excel_notes_imported
        exclude_list = ["Table 1: ", "This worksheet contains one table."]
        for word in exclude_list:
            excel_notes = excel_notes.replace(word, "")

        excel_notes = "\n".join([line.strip() for line in excel_notes.splitlines() if line.strip()])

        note = (
            f"Source of values: Export Statistics Scotland (ESS) 2023 ({data_url})\n\n"
            f"ESS Notes: {excel_notes}\n\n"
            f"Author Note: In line with ESS terminology, 'exports' denotes all outbound trade from Scotland.\n"
            f"'Non-EU' Exports are derived from Total International Exports (not shown) minus Total EU Exports.\n"
            f"Values are estimates; minor variances may occur due to source rounding (nearest 5) and regional grossing.\n\n"
            f"Last updated: {current_date}."
        )
        
        ax_note.text(0.5, 0.6, note, ha="center", va="top", fontsize=7, style="italic", color="#555555")
        
        return fig

    # 5.8 Rendering Outputs
    @render.plot
    def trade_plot():
        return create_figure()

    @render.download(
        filename=lambda: f"{datetime.now().strftime('%Y%m%d')}_Scottish_Outward_Trade_by_Destination_2008-2023_{datetime.now().strftime('%d_%b_%Y')}.pdf"
    )
    def download_pdf():
        buf = io.BytesIO()
        fig = create_figure()
        fig.savefig(buf, format="pdf", bbox_inches="tight", dpi=300)
        plt.close(fig)
        buf.seek(0)
        yield buf.getvalue()

app = App(app_ui, server)