import requests
import json
import numpy as np
import matplotlib.pyplot as plt
import io
import time
from shiny import App, render, ui
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------
# 0. DEBUG
# ---------------------------------------------------------
# Options: None, "mobile", "tablet", "desktop"

# DEBUG_SCREEN = None

# ---------------------------------------------------------
# 0. CONFIG & DATA INGESTION
# ---------------------------------------------------------
version_id = int(time.time())
this_dir = Path(__file__).parent
json_rel_path = "data/processed/clean_ESS_data.json"

if str(this_dir).startswith(("http", "https")):
    json_path = f"{this_dir}/{json_rel_path}?v={version_id}"
    web_data = requests.get(json_path).json()
else:
    with open(this_dir / json_rel_path, "r") as f:
        web_data = json.load(f)

# Global variables from JSON
years_x = web_data["years"]
ruk_vals = np.array(web_data["data"]["ruk"])
eu_vals = np.array(web_data["data"]["eu"])
non_eu_vals = np.array(web_data["data"]["non_eu"])
total_values = np.array(web_data["data"]["total"])
excel_notes = web_data["metadata"]["notes"]

data_url = "https://www.gov.scot/publications/exports-statistics-scotland-2023/"

EVENTS = {
    (2008, 2009): {"label": "Global Financial Crisis", "color": "#d9d9d9"},
    (2014, 2015): {"label": "IndyRef &\nOil Supply Chain Shock", "color": "#fff9c4"},
    (2016, 2019): {"label": "Brexit Referendum\n& consequent uncertainty", "color": "#d9d9d9"},
    (2020, 2021): {"label": "COVID-19 & New EU\nTrade Rules (TCA)", "color": "#fff9c4"},
    (2022, 2023): {"label": "Ukraine War\nEnergy Shock", "color": "#d9d9d9"}
}

# ---------------------------------------------------------
# 4. UI
# ---------------------------------------------------------
app_ui = ui.page_fluid(
    ui.div(
        ui.div(
            ui.h2("Scottish Exports by Geographical Block: 2008 - 2023",
                  style="font-weight: 900; color: #000000; margin-bottom: 5px;"),
            style="text-align: center; margin-top: 30px; margin-bottom: 10px;"
        ),
        ui.output_plot("trade_plot", height="750px"),
        ui.div(
            ui.download_button("download_pdf", "Download PDF Report"),
            ui.a("Back to GitHub", href="https://github.com/RobRodden/export_statistics_scotland", 
                 target="_blank", class_="btn btn-default", style="text-decoration: none;"),
            style="display: flex; justify-content: center; gap: 15px; margin-top: 10px; padding-bottom: 50px;"
        ),
        style="max-width: 1100px; margin: auto;"
    )
)

# ---------------------------------------------------------
# 5. SERVER
# ---------------------------------------------------------
def server(input, output, session):

    def create_figure():
        ruk_color, eu_color, non_eu_color = "#4C5B7A", "#2A9D8F", "#8ABF88"
        
        plt.style.use("default")

        # --------------------------------
        # Debug screen size simulation
        # --------------------------------

        # if DEBUG_SCREEN == "mobile":
        #     fig = plt.figure(figsize=(5, 8), layout="tight")

        # elif DEBUG_SCREEN == "tablet":
        #     fig = plt.figure(figsize=(8, 9), layout="tight")

        # elif DEBUG_SCREEN == "desktop":
        #     fig = plt.figure(figsize=(12, 10), layout="tight")

        # else:
        #     fig = plt.figure(figsize=(12, 10), layout="tight")
        
        fig = plt.figure(figsize=(12, 10), layout="tight")
        gs = fig.add_gridspec(2, 1, height_ratios=[7.5, 2.5])
        ax, ax_note = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
        ax_note.axis("off")

        x = np.arange(len(years_x))
        width = 0.25

        # Staircasing logic
        ax.set_ylim(0, total_values.max() * 1.20) 
        y_top = ax.get_ylim()[1]
        prev_x_end, state_index = None, 0
        heights = [0.96, 0.89, 0.82] 

        for (yr_start, yr_end), event in EVENTS.items():
            if yr_start in years_x or yr_end in years_x:
                idx_start = years_x.index(max(yr_start, min(years_x)))
                idx_end = years_x.index(min(yr_end, max(years_x)))
                x_center = (idx_start + idx_end) / 2
                target_y = np.interp(x_center, x, total_values) # new line
                ax.axvspan(idx_start - 0.5, idx_end + 0.5, color=event["color"], alpha=0.35, zorder=0)

                if prev_x_end is not None and abs(idx_start - prev_x_end) <= 2:
                    state_index = (state_index + 1) % 3
                else:
                    state_index = 0

                label_height = y_top * heights[state_index]
                ax.text(x_center, label_height, event["label"], ha="center", va="top",
                        fontsize=8, color="#808080", style="italic")
                ax.vlines(x=x_center, ymin=target_y, ymax=label_height - (y_top * 0.04),color="#666666", linewidth=0.6, zorder=1) # amended 
#                ax.vlines(x=x_center, ymin=total_values[idx_start:idx_end+1].mean(), 
#                          ymax=label_height - (y_top * 0.04), color="#666666", linewidth=0.6)
                prev_x_end = idx_end

        # Plotting with new variables
        b1 = ax.bar(x - width, ruk_vals, width, label="Rest of the UK", color=ruk_color, alpha=0.65, zorder=2)
        b2 = ax.bar(x, eu_vals, width, label="EU Exports", color=eu_color, alpha=0.65, zorder=2)
        b3 = ax.bar(x + width, non_eu_vals, width, label="Non-EU Exports", color=non_eu_color, alpha=0.65, zorder=2)
        line = ax.plot(x, total_values, color="#222222", marker="o", linewidth=1.5, markersize=2.3, label="Total", zorder=5)
        
        ax.set_xticks(x)
        ax.set_xticklabels(years_x)
        ax.set_ylabel("Value (£ Billions)", fontsize=11, color='#777777')
        ax.yaxis.grid(True, linestyle="--", alpha=0.25)
        for s in ['top','right','left','bottom']: ax.spines[s].set_visible(False)

        ax_note.legend([b1, b2, b3, line[0]], ["Rest of UK", "EU", "Non-EU", "Total"], 
                       loc="upper center", ncol=4, frameon=False)
        
#        note = f"Source: ESS 2023\nNotes: {excel_notes}\nUpdated: {datetime.now().strftime('%d %B %Y')}"

        note = (
            f"Source of data used: Export Statistics Scotland (ESS) 2023 ({data_url})\n\n"
            f"ESS Notes (edited): {excel_notes}\n\n"
            f"Chart Author Note: In line with ESS terminology, 'exports' denotes all outbound trade from Scotland.\n"
            f"'Non-EU' Exports are derived from Total International Exports (not shown) minus Total EU Exports.\n"
            f"Values are estimates; minor variances may occur due to source rounding (nearest 5) and regional grossing.\n\n"
            f"Last updated: {datetime.now().strftime('%d %B %Y')}."
         )
# removed {current_date} and replaced it with version_id as a test

        ax_note.text(0.5, 0.4, note, ha="center", va="top", fontsize=7, style="italic", color="#555555")

        return fig

    @render.plot
    def trade_plot():
        return create_figure()

    @render.download(
            filename=lambda: f"{datetime.now().strftime('%Y%m%d')}_Scottish_Exports_by_Geographical_Block_2008-2023_{datetime.now().strftime('%d_%b_%Y')}.pdf"
    )
    def download_pdf():
        buf = io.BytesIO()
        fig = create_figure()
        fig.savefig(buf, format="pdf")
        plt.close(fig)
        buf.seek(0)
        yield buf.getvalue()

app = App(app_ui, server)