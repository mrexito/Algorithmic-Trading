# Configuration file for the Sphinx documentation builder.
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html
from __future__ import annotations

import sys
from pathlib import Path


# -- Path setup --------------------------------------------------------------
# Add the project package so autodoc can import modules.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "Projekt"
PACKAGE_SRC = PACKAGE_ROOT / "my_trading_bot"
sys.path.insert(0, str(PACKAGE_SRC))
sys.path.insert(0, str(PACKAGE_ROOT))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "My Trading Bot Dashboard"
copyright = "2025, DIFA Projektteam"
author = "DIFA Projektteam"


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
]

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_mock_imports = [
    "dash",
    "plotly",
    "plotly.graph_objs",
    "backtrader",
    "quantstats",
    "quantstats.stats",
    "quantstats.reports",
    "yfinance",
    "psycopg2",
    "pandas",
    "numpy",
    "sklearn",
    "sklearn.linear_model",
    "sklearn.preprocessing",
    "matplotlib",
    "dtaidistance",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
language = "de"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
