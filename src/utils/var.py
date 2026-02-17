from pathlib import Path
from PIL import Image
from random import randint

APP_VERSION = "1.1.0"
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Data/images

DATA_PATH = BASE_DIR / "data" / "in"
IMAGES_PATH = BASE_DIR / "images"
FAVICON = Image.open(IMAGES_PATH / "piggybank.ico")
COVER = Image.open(IMAGES_PATH / f"cover_{randint(1,6)}.jpeg")

# Streamlit/Plotly vars

GLOBAL_STREAMLIT_STYLE = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .css-15zrgzn {display: none}
    </style>
    """

FILE_UPLOADER_CSS = """
    <style>
        [data-testid='stFileUploader'] section {
            padding: 0;
            float: left;
        }
        [data-testid='stFileUploader'] section > input + div {
            display: none;
        }
    </style>
    """


PLT_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToAdd": [
        "drawline",
        "drawopenpath",
        "drawcircle",
        "drawrect",
        "eraseshape",
    ],
    "scrollZoom": False,
}

PLT_CONFIG_NO_LOGO = {"displaylogo": False}
CACHE_EXPIRE_SECONDS = 600
PLT_FONT_SIZE = 14

# Others

TRADING_DAYS_YEAR = 252
DICT_GROUPBY_LEVELS = {
    "Macro Asset Classes": "macro_asset_class",
    "Asset Classes": "asset_class",
    "Tickers": "ticker",
}
DICT_FREQ_RESAMPLE = {
    "Year": "Y",
    "Quarter": "Q",
    "Month": "M",
    "Week": "W",
    "Day": None,
}
