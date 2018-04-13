# Instagram API

This repository has some sample code from helping CSCAR clients for extracting data from Instagram. This uses the unofficial Instagram API for Python located at https://github.com/LevPasha/Instagram-API-python.  I use the API to get the JSON response and then extract some subset of the response.

You also need the [Google Maps module](https://github.com/googlemaps/google-maps-services-python) (for geocoding) OR you can just comment out the relevant lines of code.

Example code is provided in `sample_code.py`. You need to provide your login information in `instagram_api_functions.py` before starting.

`instagram_api_functions.py` contains functions to do the following:
- Get user id for username based on exact match.
- Get timestamp of first post for user.
- Gets metadata about a user.
- Iterates through a user's timeline and extracts post and metadata.
- Downloads Instagram Media given a url.
- Iterates through a user's timeline and downloads the associated media.
- Gets media id for a given url.
- Get comments for a particular post (media).    

