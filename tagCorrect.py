import json
import re
import wikidot
import logging

logger = logging.getLogger("TagCorrect")
logger.setLevel(logging.DEBUG)
logger_handler = logging.StreamHandler()
logger_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(logger_handler)

with open("./logininfo.json", "r", encoding="utf-8") as f:
    logininfo: dict = json.load(f)

wd = wikidot.Client(logininfo["username"], logininfo["password"])
site = wd.site.get("etg-xd")
logger.info("登录成功")

if __name__ == "__main__":

    listPagesRequest = site.amc_request(
        [
            {
                "moduleName": "list/ListPagesModule",
                "category": "*",
                "order": "rating desc",
                "perPage": "100",
                "separate": "false",
                "tags": "+全自动的",
                "prependLine": "",
                "module_body": "%%title_linked%% | [{%%tags%%}]",
            }
        ]
    )
    print(listPagesRequest[0].json()["body"])
    unixlist = re.findall(r"<a href=\"/([\S]+)\">", listPagesRequest[0].json()["body"])
    taglist = re.findall(r"\[\{([ \S]+)\}\]", listPagesRequest[0].json()["body"])

    for index in range(len(unixlist)):
        for _ in range(1, 5):
            unix_name = unixlist[index]
            tags = taglist[index].replace("全自动的", "全自动")
            try:
                page_id = site.page.get(unix_name).id

                site.amc_request(
                    [
                        {
                            "action": "WikiPageAction",
                            "event": "saveTags",
                            "moduleName": "Empty",
                            "tags": tags,
                            "pageId": page_id,
                        }
                    ]
                )
                logger.info(f"{unix_name} 已添加标签 - {tags}")
            except Exception as e:
                logger.error("标签添加失败，正在重试")
                logger.error(e)
                continue
            else:
                break

    print(len(unixlist))
