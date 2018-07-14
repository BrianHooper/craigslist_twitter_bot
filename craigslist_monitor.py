"""
     Monitors a craigslist search for changes and updates new postings to twitter
"""

__author__ = "Brian Hooper"
__copyright__ = "Copyright (c) 2018 Brian Hooper"
__license__ = "MIT"
__version__ = "1.0"
__email__ = "brian_hooper@msn.com"

from bs4 import BeautifulSoup
from time import sleep
import requests
import twitter


class CraigItem:
    """Represents a single craigslist post"""
    def __init__(self, price, name, url):
        self.price = price
        self.name = name
        self.url = url

    def __str__(self):
        return self.price + ":" + self.name + " " + self.url

    def equals(self, other):
        return self.name == other.name


def get_data(url):
    """Returns a list of craigslist posts at the specified url"""
    if url is None:
        return []

    # Retrieve html
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    cr_data = soup.find_all('li', attrs={'class': 'result-row'})

    # Parse html into CraigItem objects
    craig_items = []
    for item in cr_data:
        try:
            price = item.find("span", attrs={"class": "result-price"}).text
        except AttributeError:
            price = "?"
        title = item.find("a", attrs={"class": "result-title"})
        name = title.text[:15]
        item_url = title.get("href")
        craig_item = CraigItem(price, name, item_url)
        if len(str(craig_item)) > 280:
            limit = 280 - len(craig_item.url) - len(craig_item.price) - 3
            craig_item.name = craig_item.name[:limit]
        craig_items.append(craig_item)
    return craig_items


def contains(item, elements):
    """Returns True if the item is contained in the list elements"""
    for element in elements:
        if item.equals(element):
            return True
    return False


def update_new_items(twitter_api, old_postings, new_postings):
    """Updates twitter with any posts in new_postings
    that are not also in old_postings"""
    for item in new_postings:
        if contains(item, old_postings):
            break
        else:
            try:
                twitter_api.PostUpdate(str(item))
                print("Posted " + str(item))
            except twitter.error.TwitterError:
                print("Failed to post: " + str(item))


def loop(twitter_api, cr_url, loop_seconds):
    """Continuously checks craigslist for new postings at the specified url"""
    postings = get_data(cr_url)
    while True:
        sleep(loop_seconds)
        new_postings = get_data(cr_url)
        update_new_items(twitter_api, postings, new_postings)
        postings = new_postings
        print("updating")
