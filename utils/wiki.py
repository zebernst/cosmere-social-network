from datetime import datetime


def simplify_result(result: dict) -> dict:
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
