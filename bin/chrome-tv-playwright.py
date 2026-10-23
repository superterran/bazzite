#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.58,<2"]
# ///
"""Attach to the visible Chrome TV session without closing it on disconnect."""
import argparse
import json
from playwright.sync_api import Error, sync_playwright

ENDPOINT = 'http://127.0.0.1:9223'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['status','open'], nargs='?', default='status')
    parser.add_argument('url', nargs='?')
    args = parser.parse_args()
    if args.command == 'open' and (not args.url or not args.url.startswith(('https://','http://'))):
        parser.error('open requires an http(s) URL')
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.connect_over_cdp(ENDPOINT, timeout=10000)
        except Error:
            raise SystemExit('Open "Chrome - TV & Automation" in Steam or Moonlight, then retry.') from None
        context = browser.contexts[0]
        if args.command == 'open':
            page = context.new_page()
            page.goto(args.url, wait_until='domcontentloaded')
            page.bring_to_front()
            print(json.dumps({'title':page.title(),'url':page.url}))
        else:
            # Titles only: avoid printing authenticated URLs or tokens.
            print(json.dumps({'connected':True,'pages':[{'title':p.title()} for p in context.pages]}))
        # Do not close the shared browser or its persistent default context.

if __name__ == '__main__':
    main()
