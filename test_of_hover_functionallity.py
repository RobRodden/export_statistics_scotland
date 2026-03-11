# ---------------------------------------------------------
# 6. ALTERNATIVE PLOTLY IMPLEMENTATION (FOR SHINYWEB/SHINYLIVE)
# ---------------------------------------------------------
from shiny import App, ui
from shinywidgets import output_widget, render_plotly
import plotly.graph_objects as go

# Your updated dictionary with the buttery yellow for the 'Current' period
# and descriptions for the tooltips
economic_events = {
    (2008, 2009): {"label": "Global Financial Crisis", "color": "#d9d9d9", "desc": "Collapse of RBS/HBOS and global recession."},
    (2014, 2015): {"label": "IndyRef & Oil Crash", "color": "#d9d9d9", "desc": "Referendum uncertainty + North Sea oil price collapse."},
    (2016, 2019): {"label": "Brexit Uncertainty", "color": "#d9d9d9", "desc": "Stagnant investment following the EU referendum."},
    (2020, 2021): {"label": "COVID & TCA Rules", "color": "#d9d9d9", "desc": "Pandemic lockdowns and new EU trade barriers."},
    (2022, 2024): {"label": "Energy Shock", "color": "#fff9c4", "desc": "Ukraine war impact on fuel and heating costs."}
}

app_ui = ui.page_fluid(
    ui.panel_title("Scotland Economic Timeline"),
    output_widget("timeline_plot")
)

def server(input, output, session):
    @render_plotly
    def timeline_plot():
        fig = go.Figure()

        # Add the 'Event' bars as vertical rectangles (vrect)
        for years, info in economic_events.items():
            fig.add_vrect(
                x0=years[0], x1=years[1],
                fillcolor=info["color"],
                opacity=0.5,
                layer="below",
                line_width=0,
                # This creates the 'invisible' trace that holds the tooltip
                name=info["label"],
                annotation_text=info["label"] if years[0] == 2022 else "", 
            )
            
            # Create an invisible trace for the hover tooltip
            fig.add_trace(go.Scatter(
                x=[years[0], years[1]],
                y=[0, 0], # Adjust based on your data's Y-axis range
                fill='toself',
                fillcolor='rgba(0,0,0,0)', # Invisible
                line=dict(color='rgba(0,0,0,0)'),
                name=info["label"],
                hoverinfo="text",
                hovertext=f"<b>{info['label']}</b><br>{info['desc']}",
                showlegend=False
            ))

        fig.update_layout(
            title="Economic Impact Events",
            xaxis_title="Year",
            hovermode="closest"
        )
        return fig

app = App(app_ui, server)