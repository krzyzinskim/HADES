import json

## Data settings
COUNTRIES_DIVISION = False
DIVISION_COLUMN = None
SETTINGS_DICT = None
SECTIONS = None
MAPPINGS = ["tSNE", "UMAP"]
CLUSTERINGS = ["Hierarchical", "K-Means", "HDBSCAN"]
METRIC_CHOICES = {"ir": "information radius", "hd": "Hellinger distance"}

## Streamlit settings
DEFAULT_CONFIG = {
    "displaylogo": False,
    "staticPlot": False,
    "toImageButtonOptions": {
        "height": None,
        "width": None,
    },
    "modeBarButtonsToRemove": [
        "sendDataToCloud",
        "lasso2d",
        "autoScale2d",
        "select2d",
        "zoom2d",
        "pan2d",
        "zoomIn2d",
        "zoomOut2d",
        "resetScale2d",
        "toggleSpikelines",
        "hoverCompareCartesian",
        "hoverClosestCartesian",
    ],
}

def load_settings_dict(path):
    global SETTINGS_DICT
    global SECTIONS
    global DIVISION_COLUMN
    global COUNTRIES_DIVISION
    with open(path) as f:
        SETTINGS_DICT = json.load(f)
    SECTIONS = list(SETTINGS_DICT["sections"].keys())
    DIVISION_COLUMN = SETTINGS_DICT["division_column"]
    COUNTRIES_DIVISION = DIVISION_COLUMN.lower() == "country"
    
