""" Build a list of pages on both server and cloud, then calculate redirects """

import json
import os
import sys

import requests
from json_minify import json_minify
from requests.auth import HTTPBasicAuth

CONFIG = None

def load_config():
    """ Load the config file """
    global CONFIG
    basedir = os.path.dirname(os.path.dirname(__file__))
    config_file = os.path.join(basedir, "config.jsonc")
    try:
        with open(config_file) as handle:
            CONFIG = json.loads(json_minify(handle.read()))
    except json.decoder.JSONDecodeError as exc:
        sys.exit("Unable to decode config file successfully")

def get_auth(user_key, pw_key):
    """ Return HTTP auth """
    username = CONFIG[user_key]
    password = CONFIG[pw_key]
    return HTTPBasicAuth(username, password)

def get_all_pages(server, auth, space_key):
    """ Return a dict of page names and their URLs """
    all_pages = {}
    start = 0
    while True:
        # There is a bug in the Server API which means that pagination
        # doesn't necessarily find all of the pages! Hence set the limit
        # as high as it can be.
        url = "%s/rest/api/space/%s/content?limit=500&start=%s" % (
                server, space_key, start)
        result = requests.get(url, auth=auth)
        if result.status_code != 200:
            print(url)
            print(result.text)
            sys.exit("Failed to retrieve pages from %s for %s" % (server, space_key))
        data = result.json()
        add_pages(all_pages, data)
        if data["page"]["size"] != data["page"]["limit"]:
            break
        start += data["page"]["size"]
    return all_pages

def add_pages(pages_dict, data):
    """ Add the pages to the dict """
    results = data["page"]["results"]
    for page in results:
        pages_dict[page["title"]] = page["_links"]["webui"]

def reg_escape(url):
    """ Escape special regex chars """
    url = url.replace(".", "\.")
    return url.replace("+", "\+")

load_config()
server_auth = get_auth("server_user", "server_pw")
cloud_auth = get_auth("cloud_user", "cloud_pw")
server_pages = get_all_pages(CONFIG["server_uri"], server_auth, CONFIG["space_key"])
cloud_pages = get_all_pages(CONFIG["cloud_uri"], cloud_auth, CONFIG["space_key"])
#
# Iterate through to see if any pages are missing
for page in server_pages:
    if page not in cloud_pages:
        print("WARNING! Cannot find '%s' in cloud" % page)
#
# Now produce the Apache redirects. Reverse the sort order so that if
# there are similar URLs, the longer ones get matched first.
for page in sorted(server_pages, key=server_pages.get, reverse=True):
    if page in cloud_pages:
        print('RewriteRule "^%s" "%s%s" [R=301,END]' % (
            reg_escape(server_pages[page]),
            CONFIG["cloud_uri"], cloud_pages[page]))
