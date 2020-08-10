from cx_Freeze import setup, Executable
import sys
import os.path

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages=[], excludes=["sqlite3"])
base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('main.py',
                base=base,
                icon="auto_test_main.ico"
               )
]
setup(
    name='Auto_test',
    version = '0.3',
    description = 'Auto_test',
    options = dict(build_exe = buildOptions),
    executables = executables
)