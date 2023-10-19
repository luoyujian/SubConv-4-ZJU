#!/usr/bin/env python3
# coding=utf-8
from modules import pack
from modules import parse
from modules.convert import converter
import re
from quart import Quart, request
import requests
from urllib.parse import urlencode
from hypercorn.asyncio import serve
from hypercorn.config import Config
import asyncio
import argparse

def length(sth):
    if sth is None:
        return 0
    else:
        return len(sth)

app = Quart(__name__, static_folder="static")


@app.route("/")
async def mainpage():
    return await app.send_static_file("index.html")
# route for mainpage
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
async def index(path):
    return await app.send_static_file(path)


# subscription converter api
@app.route("/sub")
async def sub():
    args = request.args
    # get interval
    if "interval" in args:
        interval = args["interval"]
    else:
        interval = "1800"

    short = args.get("short")


    # get the url of original subscription
    url = args.get("url")
    url = re.split(r"[|\n]", url)
    # remove empty lines
    tmp = list(filter(lambda x: x!="", url)) 
    url = []
    urlstandalone = []
    for i in tmp:
        if (i.startswith("http://") or i.startswith("https://")) and not i.startswith("https://t.me/"):
                url.append(i)
        else:
            urlstandalone.append(i)
    urlstandalone = "\n".join(urlstandalone)
    if len(url) == 0:
        url = None
    if len(urlstandalone) == 0:
        urlstandalone = None

    urlstandby = args.get("urlstandby")
    urlstandbystandalone = None
    if urlstandby:
        urlstandby = re.split(r"[|\n]", urlstandby)
        tmp = list(filter(lambda x: x!="", urlstandby))
        urlstandby = []
        urlstandbystandalone = []
        for i in tmp:
            if (i.startswith("http://") or i.startswith("https://")) and not i.startswith("https://t.me/"):
                urlstandby.append(i)
            else:
                urlstandbystandalone.append(i)
        urlstandbystandalone = "\n".join(urlstandbystandalone)
        if len(urlstandby) == 0:
            urlstandby = None
        if len(urlstandbystandalone) == 0:
            urlstandbystandalone = None
        
        if urlstandalone:
            urlstandalone = converter.ConvertsV2Ray(urlstandalone)
        if urlstandbystandalone:
            urlstandbystandalone = converter.ConvertsV2Ray(urlstandbystandalone)

    # get original headers
    headers = {'Content-Type': 'text/yaml;charset=utf-8'}
    # if there's only one subscription, return userinfo
    if length(url) == 1:
        originalHeaders = requests.head(url[0], headers={'User-Agent':'clash'}).headers
        if 'subscription-userinfo' in originalHeaders:  # containing info about ramaining flow
            headers['subscription-userinfo'] = originalHeaders['subscription-userinfo']
        if 'Content-Disposition' in originalHeaders:  # containing filename
            headers['Content-Disposition'] = originalHeaders['Content-Disposition'].replace("attachment", "inline")

    content = []  # the proxies of original subscriptions
    if url is not None:
        for i in range(len(url)):
            # the test of response
            respText = requests.get(url[i], headers={'User-Agent':'clash'}).text
            content.append(await parse.parseSubs(respText))
            url[i] = "{}provider?{}".format(request.url_root, urlencode({"url": url[i]}))
    if len(content) == 0:
        content = None
    if urlstandby:
        for i in range(len(urlstandby)):
            urlstandby[i] = "{}provider?{}".format(request.url_root, urlencode({"url": urlstandby[i]}))

    # get the domain or ip of this api to add rule for this
    domain = re.search(r"([^:]+)(:\d{1,5})?", request.host).group(1)
    # generate the subscription
    result = await pack.pack(url=url, urlstandalone=urlstandalone, urlstandby=urlstandby,urlstandbystandalone=urlstandbystandalone, content=content, interval=interval, domain=domain, short=short)
    return result, headers


# provider converter
@app.route("/provider")
async def provider():
    headers = {'Content-Type': 'text/yaml;charset=utf-8'}
    url = request.args.get("url")
    return await parse.parseSubs(
        requests.get(url, headers={'User-Agent':'clash'}).text
    ), headers


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-P", type=int, default=443, help="port of the api, default: 443")
    parser.add_argument("--host", "-H", type=str, default="0.0.0.0", help="host of the api, default: 0.0.0.0")
    args = parser.parse_args()
    print("host:", args.host)
    print("port:", args.port)
    # Debug
    # app.run(host=args.host, port=args.port, debug=True)
    # Production
    config = Config()
    config.bind = [f"{args.host}:{args.port}"]
    server = serve(app, config)
    asyncio.run(server)
