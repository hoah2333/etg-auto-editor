import json
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

with open("./data/gun.js", "r", encoding="utf-8") as f:
    gun: dict = json.loads(f.read()[17:])

with open("./data/gungeoneer.js", "r", encoding="utf-8") as f:
    gungeoneer: dict = json.loads(f.read()[17:])

with open("./data/room.js", "r", encoding="utf-8") as f:
    room: dict = json.loads(f.read()[17:])

with open("./data/system.js", "r", encoding="utf-8") as f:
    system: dict = json.loads(f.read()[17:])

with open("./data/synergy.js", "r", encoding="utf-8") as f:
    synergy: dict = json.loads(f.read()[17:])

with open("./data/item.js", "r", encoding="utf-8") as f:
    item: dict = json.loads(f.read()[17:])

with open("./data/shrine.js", "r", encoding="utf-8") as f:
    shrine: dict = json.loads(f.read()[17:])

with open("./data/pickup.js", "r", encoding="utf-8") as f:
    pickup: dict = json.loads(f.read()[17:])

with open("./data/quality.js", "r", encoding="utf-8") as f:
    quality: dict = json.loads(f.read()[17:])

with open("./data/chest.js", "r", encoding="utf-8") as f:
    chest: dict = json.loads(f.read()[17:])

with open("./data/enemy.js", "r", encoding="utf-8") as f:
    enemy: dict = json.loads(f.read()[17:])

with open("./data/npc.js", "r", encoding="utf-8") as f:
    npc: dict = json.loads(f.read()[17:])

with open("./data/game-mode.js", "r", encoding="utf-8") as f:
    game_mode: dict = json.loads(f.read()[17:])

with open("./data/boss.js", "r", encoding="utf-8") as f:
    boss: dict = json.loads(f.read()[17:])

with open("./data/chamber.js", "r", encoding="utf-8") as f:
    chamber: dict = json.loads(f.read()[17:])

with open("./data/page.js", "r", encoding="utf-8") as f:
    page: dict = json.loads(f.read()[17:])


def create_page(title: str, unix_name: str, source: str, tags: str):
    if unix_name == "synergy":
        unix_name = "synergies"
    if unix_name == "pickup":
        unix_name = "pickups"
    if unix_name == "achievement":
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


def add_args(key: str, item: dict[str, str], label: str):
    if key == "name" and item["locale"].get(key) is not None:
        item = item["locale"]

    return (
        (
            re.sub(r"%[0-9]{2}", "-", "\n" + f"| {label} = {value}")
            .replace("\r\n", "\n")
            .replace("自动的", "自动")
            .replace("-.", ".")
        )
        if (value := item.get(key, "")) != ""
        else ""
    )


def to_unix(string: str) -> str:
    return re.sub(r"[\.'! ]", "-", string.lower()).replace("--", "-").strip("-")


def synergies(targets: list | None) -> str:
    if targets is None:
        return ""

    text = "\n\n++ 组合"
    for target in targets:
        info = synergy[target]["locale"]
        text += f"\n* [[[synergies#{to_unix(target)}|{info.get("name", synergy[target]["name"])}]]]：{note(info["tips"].replace("\r\n", " _\n"))}"

    return text


def note(text: str | None) -> str:
    if text is None:
        return ""

    text = re.sub(r"(\r\n)+", "\n", text)
    text = text.replace("\n- ", "\n* ")
    text = text.replace("<br/>", "\n")
    for string in re.findall(r"\{\{(.*?)\}\}", text):
        if len(groups := re.split(r":", string)) != 2:
            continue

        file = groups[0].lower()
        data = eval(f"{file}['{groups[1].replace("'", "\\'")}']")
        name = data["locale"].get("name", data["name"])

        if groups[0] == "ROOM" and groups[1] == "Secret Room":
            groups[1] = "Secret Rooms"

        if groups[0] == "PICKUP":
            repl = f"[[[pickups#{to_unix(groups[1])}|{name}]]]"
        elif groups[0] == "QUALITY":
            repl = f"[[image https://7bye.com/hoah/i/etg/{data['local_icon']}]]"
        else:
            repl = f"[[[{to_unix(groups[1])}|{name}]]]"

        text = text.replace("{{" + string + "}}", repl)

    for string in re.findall(r"<h\d>.*?</h\d>", text):
        num = int(string[2])

        text = text.replace(string, f"{'+'*num} {string[4:-5]}")

    for string in re.findall(r"\[\(~+(.*?)\)\]", text):
        text = re.sub(
            r"\[\(~+(.*?)\)\]",
            f"[[image https://7bye.com/hoah/i/etg/{string}]]",
            text,
            1,
        )
        text = re.sub(r"%[0-9]{2}", "-", text).replace("-.", ".")

    for string in re.findall(r"\{(.*?)\}", text):
        text = text.replace("{" + string + "}", f"**{string}**")

    for string in re.findall(r"\(\((.*?)\)\)", text):
        text = text.replace(f"(({string}))", "{{" + string + "}}")

    for string in re.findall(r"<view.*?>(.*?)</view>", text):
        data = eval(string)
        repl = ""
        for line in data:
            for unit in line:
                if unit[0] == "~":
                    unit = "~ " + unit[1:]
                unit = unit.replace("\n", " _\n")
                repl += f"||{unit}"
            repl += "||\n"
        text = re.sub(r"<view.*?>(.*?)</view>", repl, text, 1)

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

    return f"{types.replace("自动的", "自动")} {quality} 枪械"


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
            + "\n]]\n"
            + note(locale.get("notes", locale.get("tips")))
            + synergies(target.get("synergies"))
            + "\n"
        )

        with open("./output.ftml", "at", encoding="utf-8") as output:
            print(source, file=output, end="")

        create_page(
            target["locale"].get("name", target["name"]),
            to_unix(target["name"]),
            source,
            tags_replace(target["locale"]["type"], target["quality"]),
        )


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
    add_one(gun["Cold 45"])

    """
    循环添加整个文件中的内容
    """
    # add_loop(gun.values())
