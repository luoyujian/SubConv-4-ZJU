#!/usr/bin/env python3
# coding=utf-8
from modules import pack
from modules import snippet
import re
from flask import Flask, request, render_template 
import requests
from urllib.parse import urlencode, unquote
from gevent import pywsgi
import argparse


app = Flask(__name__, static_folder="mainpage")


# route for mainpage
@app.route("/")
def index():
    return app.send_static_file("index.html")
@app.route("/index.js")
def indexjs():
    return app.send_static_file("index.js")
@app.route("/index.css")
def indexcss():
    return app.send_static_file("index.css")


# subscription converter api
@app.route("/sub")
def sub():
    args = request.args
    # get interval
    if "interval" in args:
        interval = args["interval"]
    else:
        interval = "1800"
    # get port of zju connect 
    zju = {
        "zjuPort": args.get("zjuport"),
        "zjuSocksUser": args.get("zjusocksuser"),
        "zjuSocksPasswd": args.get("zjusockspasswd"),
        "zjuAddr": args.get("zjuaddr")
    }
    short = args.get("short")

    meta = args.get("meta")  # judge if using the config of clash meta

    # get the url of original subscription
    url = args.get("url")
    url = re.split(r"[|\n]", url)
    # remove empty lines
    url = list(filter(lambda x: x!="", url)) 

    urlstandby = args.get("urlstandby")
    if urlstandby:
        urlstandby = re.split(r"[|\n]", urlstandby)
        urlstandby = list(filter(lambda x: x!="", urlstandby))

    # get original headers
    headers = {'Content-Type': 'text/yaml;charset=utf-8'}
    # if there's only one subscription, return userinfo
    if len(url) == 1:
        originalHeaders = requests.head(url[0], headers={'User-Agent':'clash'}).headers
        if 'subscription-userinfo' in originalHeaders:  # containing info about ramaining flow
            headers['subscription-userinfo'] = originalHeaders['subscription-userinfo']
        if 'Content-Disposition' in originalHeaders:  # containing filename
            headers['Content-Disposition'] = originalHeaders['Content-Disposition'].replace("attachment", "inline")

    content = []  # the proxies of original subscriptions
    for i in range(len(url)):
        # the test of response
        respText = requests.get(url[i], headers={'User-Agent':'clash'}).text
        content.append(snippet.parseSubs(respText))
        url[i] = "{}provider?{}".format(request.url_root, urlencode({"url": url[i]}))
    if urlstandby:
        for i in range(len(urlstandby)):
            urlstandby[i] = "{}provider?{}".format(request.url_root, urlencode({"url": urlstandby[i]}))

    # get the domain or ip of this api to add rule for this
    domain = re.search(r"([^:]+)(:\d{1,5})?", request.host).group(1)
    # generate the subscription
    result = pack.pack(url=url, urlstandby=urlstandby, content=content, interval=interval, domain=domain, zju=zju, meta=meta, short=short)
    return result, headers


# provider converter
@app.route("/provider")
def provider():
    headers = {'Content-Type': 'text/yaml;charset=utf-8'}
    url = request.args.get("url")
    return snippet.parseSubs(
        requests.get(url, headers={'User-Agent':'clash'}).text
    ), headers


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-P", type=int, default=443, help="port of the api, default: 443")
    parser.add_argument("--host", "-H", type=str, default="0.0.0.0", help="host of the api, default: 0.0.0.0")
    args = parser.parse_args()
    print(args.host, args.port)
    # Debug
    # app.run(host=args.host, port=args.port, debug=True)
    # Production
    server = pywsgi.WSGIServer((args.host, args.port), app)
    server.serve_forever()
