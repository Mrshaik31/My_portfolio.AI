import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

PORTFOLIO_PATH = BASE_DIR / "data" / "portfolio.json"


def load_portfolio():

    with open(
        PORTFOLIO_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        portfolio = json.load(file)

    return portfolio