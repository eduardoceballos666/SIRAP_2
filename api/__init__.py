"""API REST de SIRAP (FastAPI).

Expone la misma lógica que usa la app de Streamlit (``src/``) para un frontend independiente
(``frontend/``, Vue 3). No modifica ``src/`` ni la app de Streamlit: ambas interfaces pueden
guardar vehículos, autorizaciones y operaciones en archivos CSV locales.
"""

__version__ = "2.0.0"
