# Confluence Space Redirects

A simple script to scan *all global spaces* on Confluence Server/Data Centre and on Confluence Cloud then produce the necessary redirects for the pages.

## Requirements

* Python 3
* pipenv

## Setting up

Copy `config.sample.jsonc` to `config.jsonc`. Edit it as required, replacing `<your email address>`, `<your password>`, `<your API token>` as appropriate.

If you don't already have an API token for Confluence Cloud, go to <https://id.atlassian.com/manage-profile/security/api-tokens> and click on "Create API token".

**NOTE!** The credentials used *must* have access to all pages in the space otherwise the list of redirects will be incomplete.

## Running the script

``` Python
pipenv install
pipenv run python build_redirects_list.py
```

The script will emit a series of Apache redirect rules to the console. If the script runs without errors, run it again, redirecting output to a file and then send that file to IT Services so that the rules can be implemented on the server.
