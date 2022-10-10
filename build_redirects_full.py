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

def get_all_spaces_keys(server, auth):
    space_keys = []
    url = "%s/rest/api/space?limit=2000" % (server)
    spaces = requests.get(url, auth=auth)
    if spaces.status_code != 200:
        print(url)
        print(spaces.text)
        sys.exit("Failed to retrieve URL %s" % (url))
    data = spaces.json()
    results = data["results"]
    for space_key in results:
        if space_key["type"] == "global":
            space_keys.append(space_key["key"])
    return space_keys

def get_all_space_pages(server, auth, space_key):
    """ Return a dict of page names and their URLs """
    all_pages = {}
    start = 0
    while True:
        # There is a bug in the Server API which means that pagination
        # doesn't necessarily find all of the pages! Hence set the limit
        # as high as it can be.
        url = "%s/rest/api/space/%s/content?limit=2000&start=%s" % (
                server, space_key, start)
        result = requests.get(url, auth=auth)
        if result.status_code != 200:
            print(url)
            print(result.text)
            sys.exit("Failed to retrieve pages from %s for %s" % (server, space_key))
        data = result.json()
        add_pages(all_pages, data)
        # add_pages_tinyui(all_pages, data)
        if data["page"]["size"] != data["page"]["limit"]:
            break
        start += data["page"]["size"]
    return all_pages

def add_pages(pages_dict, data):
    """ Add the pages to the dict """
    results = data["page"]["results"]
    for page in results:
        pages_dict[page["title"]] = [page["_links"]["webui"],page["_links"]["tinyui"]]

def add_pages_tinyui(pages_dict, data):
    """ Add the pages to the dict """
    results = data["page"]["results"]
    for page in results:
        pages_dict[page["title"]] = page["_links"]["tinyui"]

def reg_escape(url):
    """ Escape special regex chars """
    url = url.replace(".", "\.")
    return url.replace("+", "\+")

def process_standard_page(page):
    """ Output a redirect for a normal page """
    print('RewriteRule "^%s" "%s%s" [R=301,END]' % (
        reg_escape(server_pages[page][0]),
        CONFIG["cloud_uri"], cloud_pages[page][0]))
    print('RewriteRule "^%s" "%s%s" [R=301,END]' % (
        reg_escape(server_pages[page][1]),
        CONFIG["cloud_uri"], cloud_pages[page][1]))

def process_query_string(page):
    """ Process a URL with a pageId in it """
    # Split the URL on the question mark
    parts = server_pages[page][0].split("?")
    # Output the conditional
    print('RewriteCond %{QUERY_STRING} ^' + parts[1] + '$')
    # then the redirect
    print('RewriteRule "^%s" "%s%s?" [R=301,END]' % (
        reg_escape(parts[0]),
        CONFIG["cloud_uri"], cloud_pages[page][0]))
    print('RewriteRule "^%s" "%s%s" [R=301,END]' % (
        reg_escape(server_pages[page][1]),
        CONFIG["cloud_uri"], cloud_pages[page][1]))

load_config()
server_auth = get_auth("server_user", "server_pw")
cloud_auth = get_auth("cloud_user", "cloud_pw")

spaces_keys = get_all_spaces_keys(CONFIG["server_uri"], server_auth)

for space_key in spaces_keys:
    print ("# Redirects for space: '%s'" % space_key)
    server_pages = get_all_space_pages(CONFIG["server_uri"], server_auth, space_key)
    cloud_pages = get_all_space_pages(CONFIG["cloud_uri"], cloud_auth, space_key)
    #
    # Iterate through to see if any pages are missing
    for page in server_pages:
        if page not in cloud_pages:
            print("WARNING! Cannot find '%s' in cloud" % page)
    #
    # Now produce the Apache redirects. Reverse the sort order so that if
    # there are similar URLs, the longer ones get matched first.
    for page in sorted(server_pages, key=server_pages.get, reverse=True):
        #print (server_pages[page][0])
        if page in cloud_pages:
            if "viewpage.action?pageId" in server_pages[page][0]:
                process_query_string(page)
            else:
                process_standard_page(page)
    
    # Add a final redirect for the space root
    print('RewriteRule "^/display/%s" "%s/spaces/%s" [R=301,END]' % (
        space_key, CONFIG["cloud_uri"], space_key))
