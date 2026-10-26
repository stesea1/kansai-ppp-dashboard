"""Offline preview: block all network requests, render web/index.html, save preview.png (+ preview_facility.png)."""
import asyncio, sys
from playwright.async_api import async_playwright
P='/workspace/ppp-dashboard/'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome'); pg = await b.new_page(viewport={'width':1500,'height':1900})
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e))); blocked=[]
        async def route(r):
            if r.request.url.startswith('file://'): await r.continue_()
            else: blocked.append(r.request.url); await r.abort()
        await pg.route('**/*', route)
        await pg.goto('file://'+P+'web/index.html'); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=P+'preview.png', full_page=True)
        await pg.select_option('#met', 'fac_waste'); await pg.select_option('#ver', 'v1'); await pg.wait_for_timeout(800)
        await pg.screenshot(path=P+'preview_facility.png', full_page=True)
        n = await pg.evaluate("document.querySelectorAll('#u tr').length-1")
        print('errors', errs, 'blocked', blocked, 'untapped rows', n)
        await b.close()
asyncio.run(main())
