
import time

from ratelimiter import RateLimiter

def limited(until):
    duration = int(round(until - time.time()))
    print('Rate limited, sleeping for {:d} seconds'.format(duration))

rate_limiter = RateLimiter(max_calls=100, period=120, callback=limited)


def flattenList(data):
    results = []
    for rec in data:
        if isinstance(rec, list):
            results.extend(rec)
            results = flattenList(results)
        else:
            results.append(rec)
    return results


