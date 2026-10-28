La aplicación vive en ``app/app.py`` (estructura pedida en el proyecto final). Este archivo existe
para que el despliegue actual, configurado con ``app.py`` en la raíz, siga funcionando sin cambios.

Localmente se puede ejecutar cualquiera de los dos::

    streamlit run app.py
    streamlit run app/app.py
"""

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).parent / "app" / "app.py"), run_name="__main__")
