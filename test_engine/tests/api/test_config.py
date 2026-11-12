from pathlib import Path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.config import get_config, save_config, reload_config

cfg = get_config()
print('Initial:', cfg['paths'])

cfg['paths']['warehouse_file'] = 'D:\\test.xlsx'
save_config(cfg)
print('Saved.')

cfg2 = reload_config()
print('Reloaded:', cfg2['paths'])
