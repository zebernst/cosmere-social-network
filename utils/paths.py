from pathlib import Path

# key paths in project
root_dir = Path(__file__).parent.parent
data_dir = root_dir / 'data'
site_dir = root_dir / 'docs'
log_dir = root_dir / 'logs'

coppermind_cache_path = root_dir / 'data' / 'cache' / 'coppermind.json'

# ensure paths exist
log_dir.mkdir(exist_ok=True)
