import tweepy
import HTMLParser
import os
import urllib2
from pycorpora import humans
from bs4 import BeautifulSoup
from time import gmtime, strftime
from wordfilter import Wordfilter
from offensive import tact
from textblob import TextBlob
from textblob.np_extractors import FastNPExtractor
from textblob.taggers import NLTKTagger
from secrets import *
from textblob import Blobber



# Bot configuration

bot_username = 'LoffInTheTimeOf'
logfile_name = bot_username + ".log"

# Twitter authentication
auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)
api = tweepy.API(auth)
tweets = api.user_timeline(bot_username)

# Global
hparser = HTMLParser.HTMLParser()
wordfilter = Wordfilter()
extractor = FastNPExtractor()
tb = Blobber(pos_tagger=NLTKTagger())
LOFF = "Love in the Time of"


def get_news():
    try:
        request = urllib2.Request(
            "http://news.google.com/news?pz=1&cf=all&ned=us&hl=en&output=rss")
        response = urllib2.urlopen(request)
    except urllib2.URLError as e:
        print(e.reason)
    else:
        html = BeautifulSoup(response.read(), "html.parser")
        items = html.find_all('item')
        for item in items:
            headline = item.title.string
            h_split = headline.split()

            # skip incomplete headlines
            if "..." in headline:
                continue

            # skip headlines in all caps
            if count_caps(h_split) >= len(h_split) - 3:
                continue

            # filter for offensive words
            if wordfilter.blacklisted(headline):
                continue

            # filter again
            if not tact(headline):
                continue

            # remove article attributions
            if "-" in headline:
                headline = headline.split("-")[:-1]
                headline = ' '.join(headline).strip()

            if process(headline):
                break
            else:
                continue


def is_adj(word_pos_tuple):
    if 'J' in word_pos_tuple[1][0]:
        return True


def is_noun(word_pos_tuple):
    if 'N' in word_pos_tuple[1][0]:
        return True

def is_proper_noun(word_pos_tuple):
    if 'NP' in word_pos_tuple[1]:
        return True

def contains_name(phrase):
    words = phrase.split()
    for w in words:
        if w.title() in humans.firstNames["firstNames"]:
            return True
        elif w.title() in humans.lastNames["lastNames"]:
            return True


def process(headline):
    text = ""
    headline = hparser.unescape(headline).strip()

    blob = tb(headline)
    n_phrases = blob.noun_phrases


    for i, phrase in enumerate(n_phrases):
        # skip if phrase is one short word
        if len(phrase) < 3:
            continue

        # skip if phrase contains 's
        if "'s" in phrase:
            continue

        # skip if phrase is a celebrity name
        if phrase.title() in humans.celebrities["celebrities"]:
            continue

        # skip if phrase is a British celebrity name
        if phrase.title() in humans.britishActors["britishActors"]:
            continue

        # skip if phrase is name of science
        if phrase.title() in humans.scientists["scientists"]:
            continue

        # skip is phrase contains first or last names
        if contains_name(phrase):
            continue

        if len(phrase.split()) > 1:
            text = LOFF + " " + phrase.title()
            print("\n====TWEET=====\n%s" % text)

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
        f.write("\n" + t + " %s" % message)


if __name__ == "__main__":
    get_news()

