from cx_Freeze import setup, Executable
import sys
import os

import lib.load_db as load_db

if not os.path.isfile("data\data.db"):
    print 'Database not found. Building database from raw files...'
    data_path = raw_input('Please provide the path to the raw data folder: ')
    db_path = os.getcwd() + '\data/data.db' 

    load_db.main(data_path, db_path)                

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
