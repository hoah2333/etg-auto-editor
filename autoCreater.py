import json
import os
import re
import wikidot
import logging

logger = logging.getLogger("AutoCreater")
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
data_dic: dict[str, dict] = {}
percent = re.compile(r"%[0-9]{2}")
links: dict[str, list[str]] = {}

for file in os.listdir("./data"):
    if ".js" in file and file not in ["conf.js"]:
        with open(f"./data/{file}", "r", encoding="utf-8") as f:
            data_dic[file.replace(".js", "").replace("-", "_")] = json.loads(
                f.read()[17:]
            )


def create_page(title: str, unix_name: str, source: str, tags: str):
    match unix_name:
        case "synergy":
            unix_name = "synergies"
        case "pickup":
            unix_name = "pickups"
        case "achievement":
            unix_name = "achievements"
    for _ in range(1, 5):
        try:
            page_id = site.page.get(unix_name)
        except wikidot.common.exceptions.NotFoundException:
            lock = site.amc_request(
                [
                    {
                        "mode": "page",
                        "wiki_page": unix_name,
                        "moduleName": "edit/PageEditModule",
                    }
                ]
            )[0].json()
            for _ in range(1, 5):
                try:
                    site.amc_request(
                        [
                            {
                                "action": "WikiPageAction",
                                "event": "savePage",
                                "moduleName": "Empty",
                                "title": title,
                                "source": source,
                                "mode": "page",
                                "wiki_page": unix_name,
                                "lock_id": lock["lock_id"],
                                "lock_secret": lock["lock_secret"],
                                "comments": f"自动新建页面：{title}",
                            }
                        ]
                    )
                    logger.info(f"{unix_name} 已创建")
                except Exception as e:
                    logger.error("创建页面失败，正在重试")
                    logger.error(e)
                    continue
                else:
                    break

            for _ in range(1, 5):
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
                    logger.info(f"{unix_name} 已添加标签")
                except Exception as e:
                    logger.error("标签添加失败，正在重试")
                    logger.error(e)
                    continue
                else:
                    break
            break
        except Exception as e:
            logger.error(f"未知错误")
            logger.error(e)
            continue
        else:
            logger.info(f"{unix_name} 已存在")

            lock = site.amc_request(
                [
                    {
                        "mode": "page",
                        "wiki_page": unix_name,
                        "moduleName": "edit/PageEditModule",
                    }
                ]
            )[0].json()

            for _ in range(1, 5):
                try:
                    site.amc_request(
                        [
                            {
                                "action": "WikiPageAction",
                                "event": "savePage",
                                "moduleName": "Empty",
                                "title": title,
                                "source": source,
                                "mode": "page",
                                "wiki_page": unix_name,
                                "lock_id": lock["lock_id"],
                                "lock_secret": lock["lock_secret"],
                                "revision_id": lock["page_revision_id"],
                                "comments": "Data corrected by AutoCreater",
                            }
                        ]
                    )
                    logger.info(f"{unix_name} 已修改内容")
                except Exception as e:
                    logger.error("内容修改失败，正在重试")
                    logger.error(e)
                    continue
                else:
                    break
            break


def add_args(key: str, item: dict[str, str], label: str) -> str:
    if key == "name" and "locale" in item and key in item["locale"]:
        item = item["locale"]

    return (
        (percent.sub("-", "\n" + f"| {label} = {info_note(str(value))}"))
        if (value := item.get(key, "")) != ""
        else ""
    )


def info_note(text: str | None) -> str:
    if text is None:
        return ""

    text = re.sub(r"(\r\n)+", "\n", text.replace("-.", "."))
    for string in re.findall(r"\{\{(.*?)\}\}", text):
        if len(groups := re.split(r":", string)) != 2:
            continue

        file = groups[0].lower()
        data = data_dic[file][groups[1]]
        name = data["locale"].get("name", data["name"])

        if groups[0] == "ROOM" and groups[1] == "Secret Room":
            groups[1] = "Secret Rooms"

        if groups[0] == "PICKUP":
            repl = f"[/pickups#{to_unix(groups[1])} {name}]"
        elif groups[0] == "QUALITY":
            repl = f"[[image https://7bye.com/hoah/i/etg/{data['local_icon']}]]"
        else:
            repl = f"[/{to_unix(groups[1])} {name}]"

        text = text.replace("{{" + string + "}}", repl)
    return text


def to_unix(string: str) -> str:
    return re.sub(r"[.'! ]+", "-", string.lower()).strip("-")


def synergies(targets: list | None) -> str:
    if targets is None:
        return ""

    text = "\n\n++ 组合"
    for target in targets:
        info: dict = data_dic["synergy"][target]["locale"]
        text += f"\n* [/synergies#{to_unix(target)} {info.get("name", data_dic["synergy"][target]["name"])}]：{note(info["tips"].replace("\r\n", " _\n"))}"

    return text


def note(text: str | None) -> str:
    if text is None:
        return ""

    text = info_note(text.replace("<br/>", "\n").replace("\n- ", "\n* "))

    for string in re.findall(r"<h\d>.*?</h\d>", text):
        num = int(string[2])

        text = text.replace(string, f"{'+'*num} {string[4:-5]}")

    patt = re.compile(r"\[\(~+(.*?)\)\]")
    for string in patt.findall(text):
        text = patt.sub(
            f"[[image https://7bye.com/hoah/i/etg/{string}]]",
            text,
            1,
        )
        text = percent.sub("-", text).replace("-.", ".")

    for string in re.findall(r"\{(.*?)\}", text):
        text = text.replace("{" + string + "}", f"**{string}**")

    for string in re.findall(r"\(\((.*?)\)\)", text):
        text = text.replace(f"(({string}))", "{{" + string + "}}")

    patt = re.compile(r"<view.*?>(.*?)</view>")
    for string in patt.findall(text):
        data = eval(string)
        repl = ""
        for line in data:
            for unit in line:
                if unit[0] == "~":
                    unit = "~ " + unit[1:]
                unit = unit.replace("\n", " _\n")
                repl += f"||{unit}"
            repl += "||\n"
        text = patt.sub(repl, text, 1)

    patt = re.compile(r"<span(.*?)>")
    for string in patt.findall(text):
        text = patt.sub(f"[[span{string}]]", text, 1)
    text = text.replace("</span>", "[[/span]]")

    text = text.replace("<g>", '[[span class="group"]]').replace("</g>", "[[/span]]")

    return text


def tags_replace(types: str | None, quality: str | None) -> str:
    if types is None:
        types = ""

    if quality == "N" or quality is None:
        quality = ""
    elif quality == "DS":
        quality = "枪械品质d 枪械品质s"
    else:
        quality = f"枪械品质{quality}"

    return f"{types} {quality} 枪械"


def add_one(target: dict):
    locale = target["locale"]
    source = (
        "[[include component:infobox"
        + add_args("name", target, "title")
        + add_args("icon", target, "img")
        + add_args("type", locale, "type")
        + add_args("quality", target, "quality")
        + add_args("magazine_size", target, "clipsize")
        + add_args("ammo_capacity", target, "maxammo")
        + add_args("reload_time", target, "reload")
        + add_args("dps", target, "dps")
        + add_args("damage", target, "damage")
        + add_args("fire_rate", target, "firerate")
        + add_args("shot_speed", target, "shotspeed")
        + add_args("charge", target, "charge")
        + add_args("range", target, "range")
        + add_args("force", target, "force")
        + add_args("spread", target, "spread")
        + add_args("sell", target, "sell")
        + add_args("unlock", locale, "unlock")
        + "\n]]\n"
        + note(locale.get("notes", locale.get("tips")))
        + synergies(target.get("synergies"))
    )

    with open("./output.ftml", "w", encoding="utf-8") as output:
        print(source, file=output, end="")

    create_page(
        target["locale"].get("name", target["name"]),
        to_unix(target["name"]),
        source,
        tags_replace(target["locale"]["type"], target["quality"]),
    )


def add_loop(table: dict):
    with open("./output.ftml", "w", encoding="utf-8") as output:
        print("", file=output, end="")

    for target in table:
        add_one(target)


def add_special(target: dict):
    locale = target["locale"]
    source = note(locale.get("notes", locale.get("tips")))

    with open("./output.ftml", "w", encoding="utf-8") as output:
        print(source, file=output, end="")

    create_page(
        target["locale"].get("name", target["name"]),
        to_unix(target["name"]),
        source,
        "",  # 暂时不添加标签
    )


if __name__ == "__main__":
    """
    添加某文件中的某个键的内容
    """
    add_one(data_dic["gun"]["Blasphemy"])

    """
    循环添加整个文件中的内容
    """
    # add_loop(gun.values())
