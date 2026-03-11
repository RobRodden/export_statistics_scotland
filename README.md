# Export Statistics Scotland (ESS) Dashboard 2023

An interactive dashboard built with **Shiny for Python** and deployed via **Shinylive** (WebAssembly). This tool visualizes Scottish export trends ("exports" as defined by the publishers) to the EU and Non-EU International markets and the Rest of the UK.

## Live Demo
https://robrodden.github.io/export_statistics_scotland/

## Key Features
* **Interactive Visualization:** Tracks trade value in £ Billions across three main destination blocks.
* **Contextual Annotations:** Highlights major economic events (Brexit, COVID-19, Ukraine War) using a dynamic "staircase" labeling system.
* **Exportable Chart:** Users can download a high-resolution PDF of the current chart.

## Tech Stack
* **Language:** Python 3.x
* **Framework:** Shiny for Python
* **Deployment:** Shinylive (Serverless/GitHub Pages)
* **Libraries:** Pandas, Matplotlib, Seaborn

## Local Development
To run this project locally:
1. Clone the repo: `git clone <your-repo-url>`
2. Install dependencies: `see requirements.txt`
3. Export the app: `shinylive export . docs`
4. Serve locally: `python3 -m http.server --directory docs --bind localhost 8008`

## REMEMBER TO ADD DEVELOPMENT LOG