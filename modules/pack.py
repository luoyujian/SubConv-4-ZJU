"""
This module is to general a complete config for Clash
"""


from modules import parse
from modules import head
import config
import yaml
import cache


def pack(url: list, urlstandby, content: str, interval, domain, short):
    regionDict, total = parse.mkList(content)  # regions available and corresponding group name
    # result = ""
    result = {}

    # create a snippet containing region groups
    # regionGroups = ""
    regionGroups = []
    # for i in total.values():
    #     regionGroups += "      - " + i[1] + "\n"
    # regionGroups = regionGroups[:-1]
    for i in total.values():
        regionGroups.append(i[1])
    

    if short is None:
        # head of config
        # result += head.HEAD
        # result += "\n"
        result.update(head.HEAD)

        # dns
        # result += head.DNS
        # result += "\n"
        result.update(head.DNS)


    # proxy providers
    # result += head.PROVIDER_HEAD
    providers = {
        "proxy-providers": {}
    }
    # for u in range(len(url)):
    #     result += head.PROVIDER_BASE0.format(u, url[u], interval, u)
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

    # if urlstandby:
    #     for u in range(len(urlstandby)):
    #         result += head.PROVIDER_BASE0.format("sub"+str(u), urlstandby[u], interval, "sub"+str(u))
    # result += "\n"
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
    result.update(providers)

    # result += head.PROXY_GROUP_HEAD
    proxyGroups = {
        "proxy-groups": []
    }
    
    # add proxy select
    # tmp = "\n"
    # for group in config.custom_proxy_group:
    #     if group["type"] == "load-balance":
    #         tmp += "      - " + group["name"] + "\n"
    # tmp += regionGroups
    # result += head.PROXY_GROUP_PROXY_SELECT.format(tmp)
    proxyGroups["proxy-groups"].append({
        "name": "🚀 节点选择",
        "type": "select",
        "proxies": [
            "♻️ 自动选择",
            "🔯 故障转移",
        ]
    })
    for group in config.custom_proxy_group:
        if group["type"] == "load-balance":
            proxyGroups["proxy-groups"][0]["proxies"].append(group["name"])
    proxyGroups["proxy-groups"][0]["proxies"].extend(regionGroups)
    proxyGroups["proxy-groups"][0]["proxies"].append("🚀 手动切换")
    proxyGroups["proxy-groups"][0]["proxies"].append("DIRECT")
    

    # add manual select
    # subscriptions = ""
    # for u in range(len(url)):
    #     subscriptions += "      - subscription" + str(u) + "\n"
    # standby = subscriptions
    # if urlstandby:
    #     for u in range(len(urlstandby)):
    #         standby += "      - subscriptionsub" + str(u) + "\n"
    # standby = standby[:-1]
    # subscriptions = subscriptions[:-1]
    # result += head.PROXY_GROUP_PROXY_MANUAL_SELECT.format(standby)
    subscriptions = []
    for u in range(len(url)):
        subscriptions.append("subscription{}".format(u))
    standby = subscriptions.copy()
    if urlstandby:
        for u in range(len(urlstandby)):
            standby.append("subscriptionsub{}".format(u))
    proxyGroups["proxy-groups"].append({
        "name": "🚀 手动切换",
        "type": "select",
        "use": standby
    })

    # add auto select
    # result += head.PROXY_GROUP_PROXY_AUTO_SELECT.format(subscriptions)
    proxyGroups["proxy-groups"].append({
        "name": "♻️ 自动选择",
        "type": "url-test",
        "url": "https://www.apple.com/library/test/success.html",
        "interval": 60,
        "tolerance": 50,
        "use": subscriptions
    })

    # add fallback
    # result += head.PROXY_GROUP_PROXY_FALLBACK.format(subscriptions)
    proxyGroups["proxy-groups"].append({
        "name": "🔯 故障转移",
        "type": "fallback",
        "url": "https://www.apple.com/library/test/success.html",
        "interval": 60,
        "tolerance": 50,
        "use": subscriptions
    })

    # add proxy groups
    # for group in config.custom_proxy_group:
    #     type = group["type"]
    #     if type == "load-balance":
    ##         region = group.get("region")
    #         if region is None:
    #             result += head.PROXY_GROUP_PROXY_ANYCAST.format(group["name"], subscriptions)
    #         else:
    #             tmp = []
    #             for i in region:
    #                 if i in total:
    #                     tmp.append(total[i][0])
    #             if len(tmp) > 0:
    #                 result += head.PROXY_GROUP_PROXY_ANYCAST.format(group["name"], subscriptions)
    #                 result += "    filter: \"{}\"".format("|".join(tmp))
    #                 result += "\n"

    #     elif type == "select":
    #         prior = group["prior"]
    #         if prior == "DIRECT":
    #             result += head.PROXY_GROUP_DIRECT_FIRST.format(group["name"], regionGroups)
    #         elif prior == "REJECT":
    #             result += head.PROXY_GROUP_REJECT_FIRST.format(group["name"], regionGroups)
    #         else:
    #             result += head.PROXY_GROUP_PROXY_FIRST.format(group["name"], regionGroups)
    for group in config.custom_proxy_group:
        type = group["type"]
        if type == "load-balance":
            region = group.get("region")
            if region is None:
                proxyGroups["proxy-groups"].append({
                    "name": group["name"],
                    "type": "load-balance",
                    "strategy": "consistent-hashing",
                    "url": "https://www.apple.com/library/test/success.html",
                    "interval": 60,
                    "tolerance": 50,
                    "use": subscriptions
                })
            else:
                tmp = []
                for i in region:
                    if i in total:
                        tmp.append(total[i][0])
                if len(tmp) > 0:
                    proxyGroups["proxy-groups"].append({
                        "name": group["name"],
                        "type": "load-balance",
                        "strategy": "consistent-hashing",
                        "url": "https://www.apple.com/library/test/success.html",
                        "interval": 60,
                        "tolerance": 50,
                        "use": subscriptions,
                        "filter": "|".join(tmp)
                    })
        
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
    # for i in total:
    #     result += head.PROXY_GROUP_REGION_GROUPS.format(total[i][1], subscriptions)
    #     result += "    filter: \"{}\"".format(total[i][0])
    #     result += "\n"
    # result += "\n"
    for i in total:
        proxyGroups["proxy-groups"].append({
            "name": total[i][1],
            "type": "url-test",
            "url": "https://www.apple.com/library/test/success.html",
            "interval": 60,
            "tolerance": 50,
            "use": subscriptions,
            "filter": total[i][0]
        })
    print(proxyGroups["proxy-groups"][-1])

    result.update(proxyGroups)

    # rules
    yaml.SafeDumper.ignore_aliases = lambda *args : True
    result = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    result += ("rules:\n  - DOMAIN,{},DIRECT\n".format(domain) + cache.cache)
    return result