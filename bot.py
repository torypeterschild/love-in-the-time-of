import tweepy
import HTMLParser
import os
import urllib2
from bs4 import BeautifulSoup
from topia.termextract import tag
from time import gmtime, strftime
from secrets import *


# ====== Bot configuration =================

bot_username = 'LoffInTheTimeOf'
logfile_name = bot_username + ".log"
# Twitter authentication
auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)
api = tweepy.API(auth)

# ==========================================

hparser = HTMLParser.HTMLParser()
tagger = tag.Tagger()
tagger.initialize()


LOFF = "Love in the Time of"


def get_news():
    try:
        request = urllib2.request(
            "http://news.google.com/news?pz=1&cf=all&ned=us&hl=en&output=rss")
        response = urllib2.urlopen(request)
    except urllib2.URLError as e:
        print(e.reason)
    else:
        html = BeautifulSoup(response.read())
        items = html.find_all('item')
        for item in items:
            headline = item.title.string
            h_split = headline.split()

    if "..." in headline:
        continue

    if count_caps(h_split) >= len(h_split) - 3:
        continue

    if not tact(headline):
        continue

    if "-" in headline:
        headline = headline.split("-")[:-1]
        headline = ' '.join(headline).strip()

    if process(headline):
        break
    else:
        continue


def process(headline):
    text = ""
    headline = hparser.unescape(headline).strip()
    tagged = tagger(headline)
    for i, word in enumerate(tagged):
        if is_candidate(word):
            text = LOFF + word.upper()

    if len(text) > 140:
        return False
    else:
        return tweet(text)


def tweet(text):
    for tweet in tweets:
        if text == tweet.text:
            return False

    # Send the tweet and log success or failure
    try:
        api.update_status(text)
    except tweepy.error.TweepError as e:
        log(e.message)
    else:
        log("Tweeted: " + text)


def count_caps(headline):
    count = 0
    for word in headline:
        if word[0].isupper():
            count += 1
    return count


def is_candidate(word):
    if (word[1] == 'NN' or word[1] == 'NNS') and word[0][0].isalpha \
            and len(word[0]) > 1:
        return True
    else:
        return False


def log(message):
    """Log message to logfile."""
    path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    with open(os.path.join(path, logfile_name), 'a+') as f:
        t = strftime("%d %b %Y %H:%M:%S", gmtime())
        f.write("\n" + t + " " + message)


if __name__ == "__main__":
    get_news()

    