import operator
import typing
from datetime import datetime

import requests
from tqdm import tqdm

from utils.caching import cache
from utils.logs import create_logger
from utils.paths import coppermind_cache_path


logger = create_logger('csn.utils.wiki')


@cache(coppermind_cache_path)
def coppermind_query() -> typing.List[dict]:
    """load data from coppermind.net"""
    logger.info("Beginning query of coppermind.net.")

    def batch_query():
        """function to query coppermind.net api in batches for all character pages"""
        # query generator code based on https://www.mediawiki.org/wiki/API:Query#Continuing_queries
        wiki_api = "https://coppermind.net/w/api.php"

        # get total number of pages to fetch
        r = requests.get(wiki_api, params=dict(action='query', format='json',
                                               prop='categoryinfo', titles='Category:Characters'))
        num_pages = r.json().get('query', {}).get('pages', {}).get('40', {}).get('categoryinfo', {}).get('pages')

        # query server until finished
        payload = {
            "action":        "query",
            "format":        "json",
            "prop":          "revisions",
            "generator":     "categorymembers",
            "rvprop":        "content|timestamp",
            "rvsection":     "0",
            "gcmtitle":      "Category:Characters",
            "gcmprop":       "ids|title",
            "gcmtype":       "page",
            "gcmlimit":      "50",
            "formatversion": 2
        }
        continue_data = {}
        with tqdm(total=num_pages, unit=' pages') as progress_bar:
            while continue_data is not None:
                req = payload.copy()
                req.update(continue_data)
                r = requests.get(wiki_api, params=req)
                response = r.json()
                num_results = len(response.get('query', {}).get('pages', []))
                logger.debug(f"Batch of {num_results} results received from coppermind.net.")

                if 'error' in response:
                    raise RuntimeError(response['error'])
                if 'warnings' in response:
                    print(response['warnings'])
                if 'query' in response:
                    yield response['query'].get('pages', [])

                continue_data = response.get('continue', None)
                progress_bar.update(num_results)

        logger.info("Finished query of coppermind.net.")

    return sorted((page
                   for batch in batch_query()
                   for page in batch),
                  key=operator.itemgetter('pageid'))


def extract_relevant_info(result: dict) -> dict:
    """flatten the relevant fields of an mediawiki api result into a single-level dictionary."""

    # possible null values
    page_id = result.get('pageid')
    timestamp = result.get('revisions', [{}])[0].get('timestamp')

    return {
        'pageid':    int(page_id) if page_id else None,
        'title':     result.get('title', ''),
        'timestamp': datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if timestamp else None,
        'content':   result.get('revisions', [{}])[0].get('content', '')
    }
