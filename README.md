# Confluence Space Redirects

A simple script to scan a space on Confluence Server/Data Centre and on Confluence Cloud then produce the necessary redirects for the pages.

## Setting up

Copy `config.sample.jsonc` to `config.jsonc`. Edit it as required, replacing `<your email address>`, `<your password>`, `<your API token>` and `<space key>` as appropriate.

**NOTE!** The credentials used *must* have access to all pages in the space otherwise the list of redirects will be incomplete.

## Running the script

``` Python
pipenv install
pipenv run python build_list.py
```
