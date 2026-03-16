# Import libraries for web requests, data handling, plotting, and UI
import requests
import json
import numpy as np
import matplotlib.pyplot as plt
import io
import time
from shiny import App, render, ui
from pathlib import Path
from datetime import datetime
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# Import constants (events, titles, URLs) from your external file
from constants import EVENTS, APP_TITLE, DATA_SOURCE_CREDIT, DATA_SOURCE_URL, GITHUB_URL

# ---------------------------------------------------------
# 0. DEBUG (Preserved as requested)
# ---------------------------------------------------------
# Options: None, "mobile", "tablet", "desktop"
# DEBUG_SCREEN = None

# ---------------------------------------------------------
# 1. CONFIG & DATA INGESTION
# ---------------------------------------------------------
version_id = int(time.time()) # Generate a timestamp to prevent browser caching
this_dir = Path(__file__).parent # Get the folder where this script is sitting
json_rel_path = "data_processed/clean_ESS_data.json" # Relative path to your JSON data

# Logic to load data from either a web URL or a local file
if str(this_dir).startswith(("http", "https")):
    json_path = f"{this_dir}/{json_rel_path}?v={version_id}"
    web_data = requests.get(json_path).json()
else:
    with open(this_dir / json_rel_path, "r") as f:
        web_data = json.load(f)

# Extract shared keys from the JSON structure
years_x = web_data["years"]
excel_notes = web_data["metadata"]["notes"]

# Convert 'Current Price' JSON lists into fast Numpy arrays for plotting
ruk_vals = np.array(web_data["data"]["current_value"]["ruk"])
eu_vals = np.array(web_data["data"]["current_value"]["eu"])
non_eu_vals = np.array(web_data["data"]["current_value"]["non_eu"])
total_values = np.array(web_data["data"]["current_value"]["total"])

# Convert 'Real Terms' JSON lists into Numpy arrays
real_ruk_vals = np.array(web_data["data"]["real_value"]["ruk"])
real_eu_vals = np.array(web_data["data"]["real_value"]["eu"])
real_non_eu_vals = np.array(web_data["data"]["real_value"]["non_eu"])
real_total_vals = np.array(web_data["data"]["real_value"]["total"])

# ---------------------------------------------------------
# 2. UI (User Interface)
# ---------------------------------------------------------
app_ui = ui.page_fluid(
    ui.div(
        # The Top Box: Renders the chart and its legend
        ui.div(
            ui.output_plot("trade_plot", height="500px")
        ),
        
        # The Middle Box: The toggle switch for Nominal vs Real prices
        ui.div(
            ui.input_switch("show_nominal", "Show Nominal Prices (Not Inflation Adjusted)", False),
            style="""
            display: flex;
            justify-content: center;
            align-items: center;
            white-space: nowrap;
            width: 100%;
            margin-top: 5px;
            margin-bottom: 20px;
        """
        ),

        # The Bottom Box: A separate plot output just for the text notes
        ui.div(
            ui.output_plot("notes_text_plot", height="160px"),
            style="border-top: 1px solid #eee; border-bottom: 1px solid #eee; margin-top: -20px;"
        ),

        # The Action Box: Download button and GitHub link
        ui.div(
            ui.download_button("download_pdf", "Download PDF Report"),
            ui.a("Back to GitHub", href=GITHUB_URL, target="_blank", class_="btn btn-default"),
            style="display: flex; justify-content: center; gap: 15px; margin-top: 20px; padding-bottom: 60px;"
        ),
        
        # Main Layout Constraints
        style="max-width: 1100px; margin: auto; padding-top: 20px;"
    )
)

# ---------------------------------------------------------
# 3. SERVER (Processing Logic)
# ---------------------------------------------------------
def server(input, output, session):
    # Calculate Y-axis ceiling once (highest point + 20% room for labels)
    global_y_max = max(total_values.max(), real_total_vals.max()) * 1.20
    ruk_color, eu_color, non_eu_color = "#4C5B7A", "#2A9D8F", "#8ABF88"

    # Helper function to grab the correct data based on the UI switch
    def get_active_data():
        if input.show_nominal():
            return ruk_vals, eu_vals, non_eu_vals, total_values, "Value (Billions - Current Prices)"
        else:
            return real_ruk_vals, real_eu_vals, real_non_eu_vals, real_total_vals, "Value (Billions - 2008 Real Terms)"

    # The master function that draws the visuals
    def create_figure(mode="combined"):
        active_ruk, active_eu, active_non_eu, active_total, y_label = get_active_data()
        plt.style.use("default")
        
        # --- FIX: PRE-DEFINE AX_NOTE TO AVOID UNBOUND ERROR ---
        ax_note = None

        # --------------------------------
        # Debug screen size simulation
        # --------------------------------
        # (Preserved debugging code as requested)
        # if DEBUG_SCREEN == "mobile":
        #     fig = plt.figure(figsize=(5, 8), layout="tight")
        # elif DEBUG_SCREEN == "tablet":
        #     fig = plt.figure(figsize=(8, 9), layout="tight")
        # elif DEBUG_SCREEN == "desktop":
        #     fig = plt.figure(figsize=(12, 10), layout="tight")
        # else:
        #     fig = plt.figure(figsize=(12, 10), layout="tight")

        # 3a. CANVAS SETUP
        if mode in ["combined", "chart_and_legend"]:
            fig = plt.figure(figsize=(12, 5.5 if mode == "chart_and_legend" else 10))
            gs = fig.add_gridspec(2, 1, height_ratios=[9.5, 0.5]) 
            ax = fig.add_subplot(gs[0])
            ax_note = fig.add_subplot(gs[1])
            ax_note.axis("off")
            fig.subplots_adjust(bottom=0.1, top=0.9, hspace=-0.05, left=0.05, right=0.95)
            
        elif mode == "chart_only":
            fig, ax = plt.subplots(figsize=(12, 6.5), layout="tight")
        else: 
            # This covers 'notes_text_only'
            fig, ax = plt.subplots(figsize=(12, 2.2))
            ax.axis("off")
            fig.subplots_adjust(top=1.0, bottom=0.0, left=0.05, right=0.95)

        # 3b. CHART DRAWING
        if mode in ["combined", "chart_and_legend", "chart_only"]:
            x = np.arange(len(years_x))
            width = 0.25
            ax.set_ylim(0, global_y_max)
            y_top = global_y_max
            
            prev_x_end, state_index = None, 0
            heights = [0.96, 0.89, 0.82]

            for (yr_start, yr_end), event in EVENTS.items():
                if yr_start in years_x or yr_end in years_x:
                    idx_start = years_x.index(max(yr_start, min(years_x)))
                    idx_end = years_x.index(min(yr_end, max(years_x)))
                    x_center = (idx_start + idx_end) / 2
                    target_y = np.interp(x_center, x, active_total)
                    ax.axvspan(idx_start - 0.5, idx_end + 0.5, color=event["color"], alpha=0.35, zorder=0)

                    if prev_x_end is not None and abs(idx_start - prev_x_end) <= 2:
                        state_index = (state_index + 1) % 3
                    else:
                        state_index = 0

                    label_height = y_top * heights[state_index]
                    ax.text(x_center, label_height, event["label"], ha="center", va="top", fontsize=8, color="#808080", style="italic")
                    ax.vlines(x=x_center, ymin=target_y, ymax=label_height - (y_top * 0.04), color="#666666", linewidth=0.6, zorder=1)
                    prev_x_end = idx_end

            ax.bar(x - width, active_ruk, width, color=ruk_color, alpha=0.65, zorder=2)
            ax.bar(x, active_eu, width, color=eu_color, alpha=0.65, zorder=2)
            ax.bar(x + width, active_non_eu, width, color=non_eu_color, alpha=0.65, zorder=2)
            ax.plot(x, active_total, color="#222222", marker="o", linewidth=1.5, markersize=2.3, zorder=5)
            
            ax.set_xticks(x)
            ax.set_xticklabels(years_x)
            ax.set_ylabel(y_label, fontsize=11, color='#777777')
            ax.set_title(APP_TITLE, fontsize=18, fontweight="bold", pad=20)
            ax.yaxis.grid(True, linestyle="--", alpha=0.25)
            for s in ['top','right','left','bottom']: ax.spines[s].set_visible(False)

        # 3c. LEGEND DRAWING
        # Note: ax_note is only not None in 'combined' or 'chart_and_legend' modes
        if ax_note is not None and mode in ["combined", "chart_and_legend"]:
            legend_elements = [
                Patch(facecolor=ruk_color, alpha=0.65, label='Rest of United Kingdom (RUK)'),
                Patch(facecolor=eu_color, alpha=0.65, label='European Union (EU)'),
                Patch(facecolor=non_eu_color, alpha=0.65, label='Rest of World (Non-EU)'),
                Line2D([0], [0], color='#222222', marker='o', markersize=4, label='Total Scotland (RUK + EU + Non-EU)')
            ]
            ax_note.legend(handles=legend_elements, loc="upper center", ncol=4, frameon=False)

        # 3d. TEXT NOTES
        if mode in ["combined", "notes_text_only"]:
            # If combined, text goes in ax_note. If notes_only, text goes in ax.
            target_ax = ax_note if mode == "combined" else ax
            if target_ax is not None:
                note = (
                    f"Source of data used: {DATA_SOURCE_CREDIT} - ({DATA_SOURCE_URL})\n\n"
                    f"ESS Notes (edited): {excel_notes}\n\n"
                    f"Chart Author Note: In line with ESS terminology, 'exports' denotes all outbound trade from Scotland.\n"
                    f"'Non-EU' Exports are derived from Total International Exports (not shown) minus Total EU Exports.\n"
                    f"Values are estimates; minor variances may occur due to source rounding (nearest 5) and regional grossing.\n\n"
                    f"Last updated: {datetime.now().strftime('%d %B %Y')}."
                )
                y_pos = 0.4 if mode == "combined" else 1.0
                target_ax.text(0.5, y_pos, note, ha="center", va="top", fontsize=7, style="italic", color="#555555")

        return fig

    # 4. RENDERS: Connect the plotting logic to the UI elements
    @render.plot
    def trade_plot():
        return create_figure(mode="chart_and_legend")

    @render.plot
    def notes_text_plot():
        return create_figure(mode="notes_text_only")

    # 5. DOWNLOAD: Bundle the whole figure (combined) into a PDF file
    @render.download(
            filename=lambda: f"{datetime.now().strftime('%Y%m%d')}_Scottish_Exports_RealTerms_GeographicalBlock_2008-2023_{datetime.now().strftime('%d_%b_%Y')}.pdf"
    )
    def download_pdf():
        buf = io.BytesIO()
        fig = create_figure(mode="combined")
        fig.savefig(buf, format="pdf", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        yield buf.getvalue()

# Initialize the App
app = App(app_ui, server)

# Previous working version
# import requests
# import json
# import numpy as np
# import matplotlib.pyplot as plt
# import io
# import time
# from shiny import App, render, ui
# from pathlib import Path
# from datetime import datetime
# from matplotlib.patches import Patch
# from matplotlib.lines import Line2D

# from constants import EVENTS, APP_TITLE, DATA_SOURCE_CREDIT, DATA_SOURCE_URL, GITHUB_URL

# # ---------------------------------------------------------
# # 0. DEBUG
# # ---------------------------------------------------------
# # Options: None, "mobile", "tablet", "desktop"

# # DEBUG_SCREEN = None


# # ---------------------------------------------------------
# # 0. CONFIG & DATA INGESTION
# # ---------------------------------------------------------
# version_id = int(time.time())
# this_dir = Path(__file__).parent
# json_rel_path = "data_processed/clean_ESS_data.json"

# if str(this_dir).startswith(("http", "https")):
#     json_path = f"{this_dir}/{json_rel_path}?v={version_id}"
#     web_data = requests.get(json_path).json()
# else:
#     with open(this_dir / json_rel_path, "r") as f:
#         web_data = json.load(f)

# # Global variables from JSON
# years_x = web_data["years"]
# excel_notes = web_data["metadata"]["notes"]

# # Current Prices
# ruk_vals = np.array(web_data["data"]["current_value"]["ruk"])
# eu_vals = np.array(web_data["data"]["current_value"]["eu"])
# non_eu_vals = np.array(web_data["data"]["current_value"]["non_eu"])
# total_values = np.array(web_data["data"]["current_value"]["total"])

# # Real Terms
# real_ruk_vals = np.array(web_data["data"]["real_value"]["ruk"])
# real_eu_vals = np.array(web_data["data"]["real_value"]["eu"])
# real_non_eu_vals = np.array(web_data["data"]["real_value"]["non_eu"])
# real_total_vals = np.array(web_data["data"]["real_value"]["total"])


# # ---------------------------------------------------------
# # 4. UI
# # ---------------------------------------------------------
# app_ui = ui.page_fluid(
#     ui.div(
#         # ui.div(
#         #     ui.h2("Scottish Exports by Geographical Block: 2008 - 2023",
#         #           style="font-weight: 900; color: #000000; margin-bottom: 5px;"),
#         #     style="text-align: center; margin-top: 30px; margin-bottom: 10px;"
#         # ),
#         # Plot Output
#         ui.output_plot("trade_plot", height="800px"),
        
#         # Inside your app_ui, above the utility menu div:
#         ui.div(
#             ui.input_switch("show_real", "Show Inflation Adjusted (2008 Prices)", False),
#             style="display: flex; justify-content: center; margin-bottom: 10px;"
#         ),

#         # Utility menu
#         ui.div(
#             ui.download_button("download_pdf", "Download PDF Report"),
#             ui.a("Back to GitHub", href=GITHUB_URL, 
#                  target="_blank", class_="btn btn-default", style="text-decoration: none;"),
#             style="display: flex; justify-content: center; gap: 15px; margin-top: 10px; padding-bottom: 50px;"
#         ),
#         # Main Container Styling
#         style="""
#             max-width: 1100px;
#             margin: auto;
#             padding-top: 40px;
#         """
#     )
# )

# # ---------------------------------------------------------
# # 5. SERVER
# # ---------------------------------------------------------
# def server(input, output, session):
# # Calculate the global max once based on CURRENT prices (the highest point)
# # We add 20% padding so the event labels have room at the top
#     global_y_max = max(total_values.max(), real_total_vals.max()) * 1.20

#     def create_figure():
#         if input.show_real():
#             active_ruk = real_ruk_vals
#             active_eu = real_eu_vals
#             active_non_eu = real_non_eu_vals
#             active_total = real_total_vals
#             y_label = "Value (Billions - 2008 Real Terms)"
#         else:
#             active_ruk = ruk_vals
#             active_eu = eu_vals
#             active_non_eu = non_eu_vals
#             active_total = total_values
#             y_label = "Value (Billions - Current Prices)"

#         ruk_color, eu_color, non_eu_color = "#4C5B7A", "#2A9D8F", "#8ABF88"
        
#         plt.style.use("default")

#         # --------------------------------
#         # Debug screen size simulation
#         # --------------------------------

#         # if DEBUG_SCREEN == "mobile":
#         #     fig = plt.figure(figsize=(5, 8), layout="tight")

#         # elif DEBUG_SCREEN == "tablet":
#         #     fig = plt.figure(figsize=(8, 9), layout="tight")

#         # elif DEBUG_SCREEN == "desktop":
#         #     fig = plt.figure(figsize=(12, 10), layout="tight")

#         # else:
#         #     fig = plt.figure(figsize=(12, 10), layout="tight")
        
#         fig = plt.figure(figsize=(12, 10), layout="tight")
#         gs = fig.add_gridspec(2, 1, height_ratios=[7.5, 2.5])
#         ax, ax_note = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
#         ax_note.axis("off")

#         x = np.arange(len(years_x))
#         width = 0.25

#         # Staircasing logic
#         ax.set_ylim(0, global_y_max) 
#         y_top = global_y_max
#         prev_x_end, state_index = None, 0
#         heights = [0.96, 0.89, 0.82]

#         for (yr_start, yr_end), event in EVENTS.items():
#             if yr_start in years_x or yr_end in years_x:
#                 idx_start = years_x.index(max(yr_start, min(years_x)))
#                 idx_end = years_x.index(min(yr_end, max(years_x)))
#                 x_center = (idx_start + idx_end) / 2
#                 target_y = np.interp(x_center, x, active_total) # new line
#                 ax.axvspan(idx_start - 0.5, idx_end + 0.5, color=event["color"], alpha=0.35, zorder=0)

#                 if prev_x_end is not None and abs(idx_start - prev_x_end) <= 2:
#                     state_index = (state_index + 1) % 3
#                 else:
#                     state_index = 0

#                 label_height = y_top * heights[state_index]
#                 ax.text(x_center, label_height, event["label"], ha="center", va="top",
#                         fontsize=8, color="#808080", style="italic")
#                 ax.vlines(x=x_center, ymin=target_y, ymax=label_height - (y_top * 0.04),color="#666666", linewidth=0.6, zorder=1) # amended 
# #                ax.vlines(x=x_center, ymin=total_values[idx_start:idx_end+1].mean(), 
# #                          ymax=label_height - (y_top * 0.04), color="#666666", linewidth=0.6)
#                 prev_x_end = idx_end

#         # Plotting with new variables
#         b1 = ax.bar(x - width, active_ruk, width, label="Rest of the UK", color=ruk_color, alpha=0.65, zorder=2)
#         b2 = ax.bar(x, active_eu, width, label="EU Exports", color=eu_color, alpha=0.65, zorder=2)
#         b3 = ax.bar(x + width, active_non_eu, width, label="Non-EU Exports", color=non_eu_color, alpha=0.65, zorder=2)
#         line = ax.plot(x, active_total, color="#222222", marker="o", linewidth=1.5, markersize=2.3, label="Total", zorder=5)
        
#         ax.set_xticks(x)
#         ax.set_xticklabels(years_x)
#         ax.set_ylabel(y_label,
#                       fontsize=11,
#                       color='#777777'
#                     )
#         ax.set_title(APP_TITLE,
#                     fontsize=18,
#                     fontweight="bold",
#                     pad=20
#                     )
#         # ax.text(
#         #     0.5, 1.02,
#         #     "Data: Export Statistics Scotland",
#         #     transform=ax.transAxes,
#         #     ha='center',
#         #     fontsize=10,
#         #     color='#666666'
#         #     )
#         ax.yaxis.grid(True, linestyle="--", alpha=0.25)
#         for s in ['top','right','left','bottom']: ax.spines[s].set_visible(False)

#         ax_note.legend([b1, b2, b3, line[0]], ["Rest of United Kingdom (RUK)", "European Union (EU)", "Rest of World (Non-EU)", "Total (RUK + EU + Non-EU)"], 
#                        loc="upper center", ncol=4, frameon=False)
        
# #        note = f"Source: ESS 2023\nNotes: {excel_notes}\nUpdated: {datetime.now().strftime('%d %B %Y')}"

#         note = (
#             f"Source of data used: {DATA_SOURCE_CREDIT} - ({DATA_SOURCE_URL})\n\n"
#             f"ESS Notes (edited): {excel_notes}\n\n"
#             f"Chart Author Note: In line with ESS terminology, 'exports' denotes all outbound trade from Scotland.\n"
#             f"'Non-EU' Exports are derived from Total International Exports (not shown) minus Total EU Exports.\n"
#             f"Values are estimates; minor variances may occur due to source rounding (nearest 5) and regional grossing.\n\n"
#             f"Last updated: {datetime.now().strftime('%d %B %Y')}."
#          )
# # removed {current_date} and replaced it with version_id as a test

#         ax_note.text(0.5, 0.4, note, ha="center", va="top", fontsize=7, style="italic", color="#555555")

#         return fig

#     @render.plot
#     def trade_plot():
#         return create_figure()

#     @render.download(
#             filename=lambda: f"{datetime.now().strftime('%Y%m%d')}_Scottish_Exports_by_Geographical_Block_2008-2023_{datetime.now().strftime('%d_%b_%Y')}.pdf"
#     )
#     def download_pdf():
#         buf = io.BytesIO()
#         fig = create_figure()
#         fig.savefig(buf, format="pdf")
#         plt.close(fig)
#         buf.seek(0)
#         yield buf.getvalue()

# app = App(app_ui, server)