from pathlib import Path, PurePath
from PIL import Image
from random import randint
import os

script_running_path = str(Path(__file__).parent.resolve())
split_script_running_path = path_split = PurePath(script_running_path).parts
assets_path = str(
    os.path.join(*split_script_running_path[0 : len(split_script_running_path) - 1])
)

APP_VERSION = "1.0.0"

# Data/images

DATA_PATH = Path(assets_path, "data", "in")
FAVICON = Image.open(Path(assets_path, "images", "piggybank.ico"))
COVER = Image.open(Path(assets_path, "images", f"cover_{randint(1,6)}.jpeg"))

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
