import os, urllib2, random, tweepy, HTMLParser
from pycorpora import humans, geography
from bs4 import BeautifulSoup
from time import gmtime, strftime
from wordfilter import Wordfilter
from offensive import tact
from textblob import TextBlob
from textblob.blob import Word
from secrets import *



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

            # Skip incomplete headlines
            if "..." in headline:
                continue

            # Skip headlines in all caps
            if count_caps(h_split) >= len(h_split) - 3:
                continue

            # Filter for offensive words
            if wordfilter.blacklisted(headline):
                continue

            # Filter again
            if not tact(headline):
                continue

            # Remove article attributions
            if "-" in headline:
                headline = headline.split("-")[:-1]
                headline = ' '.join(headline).strip()

            if process(headline):
                break
            else:
                continue


def contains_name(phrase):
    words = phrase.split()
    for w in words:
        if w.title() in humans.firstNames["firstNames"]:
            return True
        elif w.title() in humans.lastNames["lastNames"]:
            return True


def ends_with_adj(phrase):
    words = phrase.split()
    last = Word(words[-1])
    if last.get_synsets():
        syns_a = last.get_synsets(pos="a")
        if len(syns_a) >= 3:
            return True


def ends_with_verb(phrase):
    words = phrase.split()
    last = Word(words[-1])
    if last.get_synsets():
        syns_v = last.get_synsets(pos="v")
        syns_n = last.get_synsets(pos="n")
        if len(syns_v) >= len(syns_n):
            return True

def is_city(phrase):
    for c in geography.us_cities["cities"]:
        if phrase.title() == c["city"]:
            return True
    for e in geography.english_towns_cities["towns"]:
        if phrase.title() == e:
            return True
    for f in geography.english_towns_cities["cities"]:
        if phrase.title() == f:
            return True


def is_country(phrase):
    for c in geography.countries["countries"]:
        if phrase.title() == c.title():
            return True


def process(headline):
    text = ""
    candidates = []
    headline = hparser.unescape(headline).strip()
    print("\nHEADLINE: %s" % headline)

    blob = TextBlob(headline)
    n_phrases = blob.noun_phrases
    print("\nNOUN PHRASES:")
    print(n_phrases)


    for i, phrase in enumerate(n_phrases):
        # Skip if phrase is one short word
        if len(phrase) < 4:
            continue

        # Skip if phrase contains 's
        if "'s" in phrase:
            continue

        # Skip if phrase is a celebrity name
        if phrase.title() in humans.celebrities["celebrities"]:
            print("\nEliminating %s: CELEBRITIES" % phrase)
            continue

        # Skip if phrase is a British celebrity name
        if phrase.title() in humans.britishActors["britishActors"]:
            print("\nEliminating %s: BRITISH ACTORS" % phrase)
            continue

        # Skip if phrase is name of science
        if phrase.title() in humans.scientists["scientists"]:
            print("\nEliminating %s: SCIENTISTS" % phrase)
            continue

        # Skip is phrase contains first or last names
        if contains_name(phrase):
            print("\nEliminating %s: CONTAINS NAME" % phrase)
            continue

        # Skip if the last word is probably a verb
        if ends_with_verb(phrase):
            print("\nEliminating %s: ENDS WITH VERB" % phrase)
            continue

        # Skip if the last word is probably an adjective
        if ends_with_adj(phrase):
            print("\nEliminating %s: ENDS WITH ADJ" % phrase)
            continue


        # Skip if phrase is city name
        if is_city(phrase):
            print("\nEliminating %s: CITY" % phrase)
            continue

        # Skip if phrase is a country name
        if is_country(phrase):
            print("\nEliminating %s: COUNTRY" % phrase)
            continue

        if len(phrase) > 5:
            candidates.append(phrase.title())

    print("\nCANDIDATES")
    print(candidates)

    if candidates:
        text = LOFF + " " + random.choice(candidates)

    # If text is too long, don't tweet
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


def log(message):
    """Log message to logfile."""
    path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    with open(os.path.join(path, logfile_name), 'a+') as f:
        t = strftime("%d %b %Y %H:%M:%S", gmtime())
        f.write("\n" + t + " %s" % message)


if __name__ == "__main__":
    get_news()

