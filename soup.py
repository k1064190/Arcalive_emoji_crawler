import random
import time

import requests
from bs4 import BeautifulSoup as Soup

global_time = time.time()


def get_soup(url, s, g_soup=True, image=False):
    global global_time
    # delay the request to avoid being blocked
    #
    curtime = time.time()
    if not image:
        if curtime - global_time < 1000:
            # sleep time with gaussian distribution of mean 1.0 and standard deviation 0.6
            time.sleep(min(max(random.gauss(0.5, 0.6), 0.25), 2.5))
            # time.sleep(random.randint(1000, 3000) / 1000)
    global_time = curtime
    try:
        res = requests.get(url, **s, timeout=15)
    except requests.exceptions.RequestException:
        return None
    if g_soup:
            res = Soup(res.text, "html.parser")
    return res
