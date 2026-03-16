![Export chart](assets/how_have_scotlands_exports_changed_between_2003_2008.png)

# Draft: Scottish Exports Dashboard (2008-2023)
## [View Live Demo](https://robrodden.github.io/export_statistics_scotland/)
*(Note: May be slow on first loading as the Python environment initialises in your browser.)*

A dynamic, interactive web application built with **Shiny for Python** to visualise Scotland's export statistics by geographical block. This tool provides insights into trade trends with the Rest of the UK (RUK), the European Union (EU), and the Rest of the World (Non-EU). [Exports as defined by the Export Statistics Scotland (ESS) 2023 publication]

## Key Features
* **Interactive Time-Series Visualisation:** Tracks trade value in £ Billions across three main destination blocks from 2008 to 2023.
* **Inflation Adjustment:** A built-in toggle to switch between **Real Terms** (inflation-adjusted to 2008 prices) and **Nominal Prices** (current value).
* **Contextual Events:** Integrated "staircase" labeling system for major economic events (Brexit, COVID-19, Ukraine War), allowing users to see their direct impact on trade data.
* **Exportable PDF:** Generate and download high-resolution PDF reports of the current chart.
* **Serverless Deployment:** Hosted via **Shinylive**, running entirely in the browser for maximum accessibility.

## Tech Stack
* **Language:** Python 3.11+
* **Framework:** Shiny for Python
* **Libraries:** NumPy, Matplotlib, Requests, and Pandas (for data processing)
* **Deployment:** Shinylive & GitHub Pages

## Project Structure
* `/app`: Contains the live application code (`app.py`), UI constants, and processed JSON data.
* `/data_processed`: Cleaned data source generated from official Scottish Government statistics.
* `/docs`: Static export of the application for GitHub Pages hosting.
* `requirements.txt`: Project dependencies.

## Local Development
1. **Clone the repo:**
```bash
    git clone https://github.com/RobRodden/export_statistics_scotland.git
    cd export_statistics_scotland
```

2. Set Up a Virtual Environment
```bash
    python -m venv venv
    
    # Windows:
    .\venv\Scripts\activate
    
    # Mac/Linux:
    source venv/bin/activate
```

3. Install dependencies:
```bash
    pip install -r requirements.txt
```

4. Run the app:
```bash
    cd app
    shiny run --reload app.py
    
    The app will be available at http://localhost:8000.
```

5. Test the Static Build (Optional):
```bash
    python3 -m http.server --directory docs 8008
    
    The static version will be available at http://localhost:8008.
```

## Data Source
Data is sourced from the Export Statistics Scotland (ESS) 2023 publication.
Source: https://www.gov.scot/publications/exports-statistics-scotland-2023/

## License
This project is licensed under the MIT License - see the LICENSE file for details.