# constants.py

# Economic Event Library for the Chart
EVENTS = {
    (2008, 2009): {"label": "Global Financial Crisis", "color": "#d9d9d9"},
    (2014, 2015): {"label": "IndyRef &\nOil Supply Chain Shock", "color": "#fff9c4"},
    (2016, 2019): {"label": "Brexit Referendum\n& consequent uncertainty", "color": "#d9d9d9"},
    (2020, 2021): {"label": "COVID-19 & New EU\nTrade Rules (TCA)", "color": "#fff9c4"},
    (2022, 2023): {"label": "Ukraine War\nEnergy Shock", "color": "#d9d9d9"}
}

# Application UI Text
APP_TITLE = "How have Scotland's exports changed between 2008–2023?"
DATA_SOURCE_CREDIT = "Export Statistics Scotland (ESS) 2023"
DATA_SOURCE_URL = "https://www.gov.scot/publications/exports-statistics-scotland-2023/"
GITHUB_URL = "https://github.com/RobRodden/export_statistics_scotland"