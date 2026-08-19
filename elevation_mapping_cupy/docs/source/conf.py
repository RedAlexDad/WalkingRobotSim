# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

html_theme = "sphinx_rtd_theme"

project = "elevation_mapping_cupy"
copyright = "2022, Takahiro Miki, Gian Erni"
author = "Takahiro Miki, Gian Erni"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    # The Jazzy branch documentation is intentionally bring-up focused. API docs are out of scope.
    "python/**",
]

html_theme_options = {
    "analytics_anonymize_ip": False,
    "logo_only": False,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    # "style_nav_header_background": "#A00000",
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

# No custom static files for this minimal documentation.
html_static_path = []
