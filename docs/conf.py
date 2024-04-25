# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

import qbraid_qir

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../../qbraid_qir"))

# -- Project information -----------------------------------------------------

project = "qbraid-qir"
copyright = "2024, qBraid Development Team"
author = "qBraid Development Team"

# The full version, including alpha/beta/rc tags
release = qbraid_qir.__version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "autodoc2",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx.ext.todo",
    "sphinx.ext.mathjax",
    "sphinx.ext.coverage",
]

# set_type_checking_flag = True
autosummary_generate = True
autodoc_member_order = "bysource"
autoclass_content = "both"
autodoc_mock_imports = ["cirq", "qasm3", "openqasm3"]
napoleon_numpy_docstring = False
todo_include_todos = True
mathjax_path = "https://cdn.jsdelivr.net/npm/mathjax@2/MathJax.js?config=TeX-AMS-MML_HTMLorMML"

# The master toctree document.
master_doc = "index"

source_suffix = ['.rst', '.md']

suppress_warnings = ["myst.strikethrough"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "*.pytest_cache",
    "*.ipynb_checkpoints",
    "*tests",
]

# A boolean that decides whether module names are prepended to all object names
# (for object types where a “module” of some kind is defined), e.g. for
# py:function directives.
add_module_names = False

# A list of prefixes that are ignored for sorting the Python module index
# (e.g., if this is set to ['foo.'], then foo.bar is shown under B, not F).
# This can be handy if you document a project that consists of a single
# package. Works only for the HTML builder currently.
modindex_common_prefix = ["qbraid_qir."]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# html_theme_options = {
#     "collapse_navigation": False
# }

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_favicon = "_static/favicon.ico"
html_show_sphinx = False

html_css_files = ["css/s4defs-roles.css"]

# -- Autodoc settings ---------------------------------------------------

autodoc2_render_plugin = "myst"
autodoc2_packages = [
    {
        "path": "../qbraid_qir",
        # "exclude_files": ["_docs.py"],
        "auto_mode": False,
    }
]
autodoc2_hidden_objects = ["dunder", "private", "inherited"]
autodoc2_replace_annotations = [
    ("re.Pattern", "typing.Pattern"),
    ("markdown_it.MarkdownIt", "markdown_it.main.MarkdownIt"),
]
autodoc2_replace_bases = [
    ("sphinx.directives.SphinxDirective", "sphinx.util.docutils.SphinxDirective"),
]
autodoc2_docstring_parser_regexes = [
    ("qbraid_qir", "myst"),
]
nitpicky = True
nitpick_ignore_regex = [
    (r"py:.*", r"docutils\..*"),
    (r"py:.*", r"pygments\..*"),
    (r"py:.*", r"typing\.Literal\[.*"),
]
nitpick_ignore = [
    ("py:obj", "myst_parser._docs._ConfigBase"),
    ("py:exc", "MarkupError"),
    ("py:class", "sphinx.util.typing.Inventory"),
    ("py:class", "sphinx.writers.html.HTMLTranslator"),
    ("py:obj", "sphinx.transforms.post_transforms.ReferencesResolver"),
]

# -- MyST settings ---------------------------------------------------

myst_enable_extensions = [
    "dollarmath",
    "amsmath",
    "deflist",
    "fieldlist",
    "html_admonition",
    "html_image",
    "colon_fence",
    "smartquotes",
    "replacements",
    "linkify",
    "strikethrough",
    "substitution",
    "tasklist",
    "attrs_inline",
    "attrs_block",
]

# -- More customizations ----------------------------------------------------


# def skip_member(app, what, name, obj, skip, options):
#     print(app, what, name, obj, skip, options)
#     return True
#
#
# def setup(app):
#     app.connect('autodoc-skip-member', skip_member)
