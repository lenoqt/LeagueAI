#!/usr/bin/python3
import requests

# This is made to comply with the status codes on Riot API
# 400	Bad request
# 401	Unauthorized
# 403	Forbidden
# 404	Data not found
# 405	Method not allowed
# 415	Unsupported media type
# 429	Rate limit exceeded
# 500	Internal server error
# 502	Bad gateway
# 503	Service unavailable
# 504	Gateway timeout

class DataGrinderError(requests.exceptions.HTTPError):
    pass
