from pathlib import Path

from .constants import book_keys


__all__ = ['root_dir', 'site_dir', 'log_dir', 'data_dir', 'cache_dir', 'book_dir', 'disambiguation_dir',
           'coppermind_cache_path', 'gml_dir', 'json_dir']


# key paths in project
root_dir: Path = Path(__file__).parent.parent
site_dir: Path = root_dir / 'docs'
log_dir: Path = root_dir / 'logs'
data_dir: Path = root_dir / 'data'
cache_dir: Path = data_dir / 'cache'
book_dir: Path = data_dir / 'books'
disambiguation_dir: Path = data_dir / 'disambiguation'

# cached data
coppermind_cache_path: Path = cache_dir / 'coppermind.json'

# generated data
gml_dir: Path = data_dir / 'networks'
json_dir: Path = site_dir / 'api' / 'data' / 'networks'

# ensure paths exist
for path in (root_dir, data_dir, site_dir, log_dir, gml_dir, json_dir, cache_dir):
    path.mkdir(parents=True, exist_ok=True)
