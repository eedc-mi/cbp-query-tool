from cx_Freeze import setup, Executable
import sys

build_options = {
    'packages' : ['sqlalchemy.dialects.sqlite'],
    'include_files' : ['data/data.db'],
    'include_msvcr' : True}

executables = [Executable('app.py', base = 'Win32GUI')]

setup(
    name='app',
    version='0.1',
    executables=executables,
    options={'build_exe' : build_options})
