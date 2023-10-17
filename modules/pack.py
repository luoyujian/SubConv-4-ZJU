"""
This module is to general a complete config for Clash
"""


from modules import parse
from modules import head
import re
import config
import yaml
import cache


def pack(url: list, urlstandalone: list, urlstandby:list, urlstandbystandalone: list, content: str, interval, domain, short):
    regionDict, total = parse.mkList(content, urlstandalone)  # regions available and corresponding group name
    result = {}

    # create a snippet containing region groups
    regionGroups = []
    for i in total.values():
        regionGroups.append(i[1])
    

    if short is None:
        # head of config
        result.update(head.HEAD)

        # dns
        result.update(head.DNS)

    # proxies
    proxies = {
        "proxies": []
    }
    proxiesName = []
    proxiesStandbyName = []

    if urlstandalone or urlstandbystandalone:
        if urlstandalone:
            for i in urlstandalone:
                proxies["proxies"].append(
                    i
                )
                proxiesName.append(i["name"])
                proxiesStandbyName.append(i["name"])
        if urlstandbystandalone:
            for i in urlstandbystandalone:
                proxies["proxies"].append(
                    i
                )
                proxiesStandbyName.append(i["name"])
    if len(proxies["proxies"]) == 0:
        proxies = None
    if len(proxiesName) == 0:
        proxiesName = None
    if len(proxiesStandbyName) == 0:
        proxiesStandbyName = None
    if proxies:
        result.update(proxies)


    # proxy providers
    providers = {
        "proxy-providers": {}
    }
    if url or urlstandby:
        if url:
            for u in range(len(url)):
                providers["proxy-providers"].update({
                    "subscription{}".format(u): {
                        "type": "http",
                        "url": url[u],
                        "interval": int(interval),
                        "path": "./sub/subscription{}.yaml".format(u),
                        "health-check": {
                            "enable": True,
                            "interval": 60,
                            # "lazy": True,
                            "url": "https://www.apple.com/library/test/success.html"
                        }
                    }
                })
        if urlstandby:
            for u in range(len(urlstandby)):
                providers["proxy-providers"].update({
                    "subscription{}".format("sub"+str(u)): {
                        "type": "http",
                        "url": urlstandby[u],
                        "interval": int(interval),
                        "path": "./sub/subscription{}.yaml".format("sub"+str(u)),
                        "health-check": {
                            "enable": True,
                            "interval": 60,
                            # "lazy": True,
                            "url": "https://www.apple.com/library/test/success.html"
                        }
                    }
                })
    if len(providers["proxy-providers"]) == 0:
        providers = None
    if providers:
        result.update(providers)

    # result += head.PROXY_GROUP_HEAD
    proxyGroups = {
        "proxy-groups": []
    }
    
    # add proxy select
    proxySelect = {
        "name": "🚀 节点选择",
        "type": "select",
        "proxies": [
            "♻️ 自动选择",
            "🔯 故障转移",
        ]
    }
    for group in config.custom_proxy_group:
        if group["type"] == "load-balance":
            proxySelect["proxies"].append(group["name"])
    proxySelect["proxies"].extend(regionGroups)
    proxySelect["proxies"].append("🚀 手动切换")
    proxySelect["proxies"].append("DIRECT")
    proxyGroups["proxy-groups"].append(proxySelect)

    

    # add manual select
    subscriptions = []
    if url:
        for u in range(len(url)):
            subscriptions.append("subscription{}".format(u))
    standby = subscriptions.copy()
    if urlstandby:
        for u in range(len(urlstandby)):
            standby.append("subscriptionsub{}".format(u))
    if len(subscriptions) == 0:
        subscriptions = None
    if len(standby) == 0:
        standby = None
    manulSelect = {
        "name": "🚀 手动切换",
        "type": "select"
    }
    if standby:
        manulSelect["use"] = standby
    if proxiesStandbyName:
        manulSelect["proxies"] = proxiesStandbyName
    proxyGroups["proxy-groups"].append(manulSelect)

    # add auto select
    autoSelect = {
        "name": "♻️ 自动选择",
        "type": "url-test",
        "url": "https://www.apple.com/library/test/success.html",
        "interval": 60,
        "tolerance": 50,
    }
    if subscriptions:
        autoSelect["use"] = subscriptions
    if proxiesName:
        autoSelect["proxies"] = proxiesName
    proxyGroups["proxy-groups"].append(autoSelect)

    # add fallback
    fallback = {
        "name": "🔯 故障转移",
        "type": "fallback",
        "url": "https://www.apple.com/library/test/success.html",
        "interval": 60,
        "tolerance": 50,
    }
    if subscriptions:
        fallback["use"] = subscriptions
    if proxiesName:
        fallback["proxies"] = proxiesName
    proxyGroups["proxy-groups"].append(fallback)

    # add proxy groups
    for group in config.custom_proxy_group:
        type = group["type"]
        if type == "load-balance":
            region = group.get("region")
            if region is None:
                loadBalance = {
                    "name": group["name"],
                    "type": "load-balance",
                    "strategy": "consistent-hashing",
                    "url": "https://www.apple.com/library/test/success.html",
                    "interval": 60,
                    "tolerance": 50,
                }
                if subscriptions:
                    loadBalance["use"] = subscriptions
                if proxiesName:
                    loadBalance["proxies"] = proxiesName
                proxyGroups["proxy-groups"].append(loadBalance)
            else:
                tmp = []
                for i in region:
                    if i in total:
                        tmp.append(total[i][0])
                if len(tmp) > 0:
                    loadBalance = {
                        "name": group["name"],
                        "type": "load-balance",
                        "strategy": "consistent-hashing",
                        "url": "https://www.apple.com/library/test/success.html",
                        "interval": 60,
                        "tolerance": 50,
                        "filter": "|".join(tmp)
                    }
                    if subscriptions:
                        loadBalance["use"] = subscriptions
                    if proxiesName:
                        loadBalance["proxies"] = proxiesName
                    proxyGroups["proxy-groups"].append(loadBalance)
                else:
                    proxyGroups["proxy-groups"][0]["proxies"].remove(group["name"])
        
        elif type == "select":
            prior = group["prior"]
            if prior == "DIRECT":
                proxyGroups["proxy-groups"].append({
                    "name": group["name"],
                    "type": "select",
                    "proxies": [
                        "DIRECT",
                        "🚀 节点选择",
                        *regionGroups,
                        "🚀 手动切换"
                    ]
                })
            elif prior == "REJECT":
                proxyGroups["proxy-groups"].append({
                    "name": group["name"],
                    "type": "select",
                    "proxies": [
                        "REJECT",
                        "DIRECT",
                        "🚀 节点选择",
                        *regionGroups,
                        "🚀 手动切换"
                    ]
                })
            else:
                proxyGroups["proxy-groups"].append({
                    "name": group["name"],
                    "type": "select",
                    "proxies": [
                        "🚀 节点选择",
                        *regionGroups,
                        "🚀 手动切换",
                        "DIRECT"
                    ]
                })

    # add region groups
    for i in total:
        urlTest = {
            "name": total[i][1],
            "type": "url-test",
            "url": "https://www.apple.com/library/test/success.html",
            "interval": 60,
            "tolerance": 50,
            "filter": total[i][0]
        }
        if subscriptions:
            urlTest["use"] = subscriptions
        if proxiesName:
            urlTestProxies = []
            for p in proxiesName:
                if re.search(
                    total[i][0],
                    p,
                    re.I
                ) is not None:
                    urlTestProxies.append(p)
            if len(urlTestProxies) > 0:
                urlTest["proxies"] = urlTestProxies
            else:
                urlTestProxies = None
        proxyGroups["proxy-groups"].append(urlTest)

    result.update(proxyGroups)

    # rules
    yaml.SafeDumper.ignore_aliases = lambda *args : True
    result = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    result += ("rules:\n  - DOMAIN,{},DIRECT\n".format(domain) + cache.cache)
    return result