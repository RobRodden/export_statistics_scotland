import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import io
from shiny import App, render, ui
from pathlib import Path
from datetime import datetime
from shinywidgets import output_widget, render_plotly
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. PATH & DATA INGESTION
# ---------------------------------------------------------
this_dir = Path(__file__).parent
data_path = this_dir / "ESS+2023+-+Published+Tables.xlsx"

metadata_df = pd.read_excel(data_path, sheet_name="Table 1 Exports by destination", nrows=3, usecols="A", header=None)
excel_notes_imported = "\n".join(metadata_df[0].astype(str).str.strip().tolist())

df = pd.read_excel(data_path, sheet_name="Table 1 Exports by destination", header=4, usecols="A:Q").dropna(how="all")

# UPDATED EVENTS: Added 'desc' for the Plotly Hover Tooltips
EVENTS = {
    (2008, 2009): {"label": "Financial Crisis", "color": "#d9d9d9", "desc": "Global banking collapse and recession."},
    (2014, 2015): {"label": "IndyRef & Oil Shock", "color": "#fff9c4", "desc": "Referendum uncertainty & North Sea oil price collapse."},
    (2016, 2019): {"label": "Brexit Uncertainty", "color": "#d9d9d9", "desc": "Stagnant investment following the EU referendum."},
    (2020, 2021): {"label": "COVID & TCA Rules", "color": "#fff9c4", "desc": "Pandemic lockdowns and new EU trade barriers."},
    (2022, 2023): {"label": "Energy Shock", "color": "#d9d9d9", "desc": "Ukraine war impact on global fuel and heating costs."}
}

# ---------------------------------------------------------
# 2. DATA CLEANING & TYPE CONVERSION
# ---------------------------------------------------------
df["Destination"] = df["Destination"].astype(str).str.strip()
for col in df.columns:
    if col != "Destination":
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.replace(" ", ""), errors="coerce")

df = df[df["Destination"].notna()]
years = [col for col in df.columns if col != "Destination"]

# 3.1 Establish 'International Non-EU'
new_row = {"Destination": "International Non-EU"}
for year in years:
    intl = df.loc[df["Destination"] == "Total International Exports", year].sum()
    eu = df.loc[df["Destination"] == "Total EU Exports", year].sum()
    new_row[year] = intl - eu
df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

# 3.3 Transformation for Plotting
summary_categories = ["Total RUK Exports", "Total EU Exports", "International Non-EU"]
df_plot = df[df["Destination"].isin(summary_categories)].copy()
df_plot = df_plot.melt(id_vars="Destination", var_name="Year", value_name="Export_Value")
df_plot["Export_Value"] = df_plot["Export_Value"] / 1000
df_plot["Year"] = df_plot["Year"].astype(int)

# ---------------------------------------------------------
# 4. USER INTERFACE (UI)
# ---------------------------------------------------------
app_ui = ui.page_fluid(
    ui.div(
        ui.panel_title("Scotland Economic Trade Dashboard"),
        # We keep both: Plotly for interaction, Plot for the PDF-ready version
        ui.navset_card_pill(
            ui.nav_panel("Interactive Explorer", output_widget("timeline_plot")),
            ui.nav_panel("Static Report", ui.output_plot("trade_plot", height="600px")),
        ),
        ui.div(
            ui.download_button("download_pdf", "Download PDF Report"),
            style="padding: 20px; text-align: center;"
        ),
        style="max-width: 1100px; margin: auto;"
    )
)

# ---------------------------------------------------------
# 5. SERVER LOGIC
# ---------------------------------------------------------
def server(input, output, session):
    
    @render_plotly
    def timeline_plot():
        fig = go.Figure()
        
        # 1. Add Bars for each category
        for cat in summary_categories:
            sub = df_plot[df_plot["Destination"] == cat]
            fig.add_trace(go.Bar(x=sub["Year"], y=sub["Export_Value"], name=cat))

        # 2. Add Background Events and Hover Hitboxes
        for (y0, y1), info in EVENTS.items():
            fig.add_vrect(
                x0=y0, x1=y1, fillcolor=info["color"], 
                opacity=0.3, layer="below", line_width=0
            )
            # Hover hitbox
            fig.add_trace(go.Scatter(
                x=[y0, y0, y1, y1], y=[0, 60, 60, 0],
                fill='toself', fillcolor='rgba(0,0,0,0)',
                line=dict(color='rgba(0,0,0,0)'),
                name=info["label"], text=f"<b>{info['label']}</b><br>{info.get('desc', '')}",
                hoverinfo="text", showlegend=False
            ))

        fig.update_layout(
            barmode='stack', 
            title="Scottish Exports with Economic Context",
            hovermode="closest",
            template="plotly_white"
        )
        return fig

    @render.plot
    def trade_plot():
        # Using your existing Matplotlib logic for the static view
        ruk_color, eu_color, non_eu_color = "#4C5B7A", "#2A9D8F", "#8ABF88"
        fig, ax = plt.subplots(figsize=(10, 6))
        pivot = df_plot.pivot(index="Year", columns="Destination", values="Export_Value")
        pivot.plot(kind='bar', stacked=True, ax=ax, color=[eu_color, non_eu_color, ruk_color])
        ax.set_title("Static Export Summary")
        return fig

    @render.download(filename=lambda: "Scotland_Trade_Report.pdf")
    def download_pdf():
        buf = io.BytesIO()
        # You would use your full 'create_figure()' logic here for the PDF
        plt.savefig(buf, format="pdf")
        buf.seek(0)
        yield buf.getvalue()

app = App(app_ui, server)