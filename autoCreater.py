from collections import Counter
import json
import os
import re
from typing import Callable
import wikidot
import logging

COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_BLUE = "\033[34m"
COLOR_RESET = "\033[0m"

IMG_SERVER = "https://7bye.com/hoah/i/etg"

logger = logging.getLogger("AutoCreater")
logger.setLevel(logging.DEBUG)
logger_handler = logging.StreamHandler()
logger_handler.setFormatter(
    logging.Formatter(
        f"{COLOR_YELLOW}%(asctime)s {COLOR_RESET}- {COLOR_YELLOW}%(name)s {COLOR_RESET}- {COLOR_BLUE}%(levelname)s {COLOR_RESET}- {COLOR_GREEN}%(message)s{COLOR_RESET}"
    )
)
logger.addHandler(logger_handler)

with open("./logininfo.json", "r", encoding="utf-8") as f:
    logininfo: dict = json.load(f)

wd = wikidot.Client(logininfo["username"], logininfo["password"])
site = wd.site.get("etg-xd")
logger.info("登录成功")
data_dic: dict[str, dict[str, str]] = {}
percent = re.compile(r"%[0-9]{2}")


for file in os.listdir("./data"):
    if ".js" in file and file not in ["conf.js"]:
        with open(f"./data/{file}", "r", encoding="utf-8") as f:
            data_dic[file.replace(".js", "").replace("-", "_")] = json.loads(
                f.read()[17:]
            )


def Retry(error_text: str, times: int = 5, ifRaise: bool = True):
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"{COLOR_RED}{error_text}")
                    logger.error(f"{COLOR_RED}{e}")
                    if ifRaise and i == times - 1:
                        raise e

        return wrapper

    return decorator


class create_page:
    @Retry("创建页面失败，正在重试", ifRaise=False)
    def create_new_page(self, ifEdit: bool = False):
        site.amc_request(
            [
                {
                    "action": "WikiPageAction",
                    "event": "savePage",
                    "moduleName": "Empty",
                    "title": self.title,
                    "source": self.source,
                    "mode": "page",
                    "wiki_page": self.unix_name,
                    "lock_id": self.lock["lock_id"],
                    "lock_secret": self.lock["lock_secret"],
                    "comments": (
                        f"自动新建页面：{self.title}"
                        if not ifEdit
                        else f"Data corrected by AutoCreater"
                    ),
                }
            ]
        )
        logger.info(
            f"{self.unix_name} 已创建" if not ifEdit else f"{self.unix_name} 已修改"
        )

    @Retry("标签添加失败，正在重试")
    def edit_tags(self):
        site.amc_request(
            [
                {
                    "action": "WikiPageAction",
                    "event": "saveTags",
                    "moduleName": "Empty",
                    "tags": self.tags,
                    "pageId": self.id,
                }
            ]
        )
        logger.info(f"{self.unix_name} 已添加标签")

    @Retry("创建编辑锁失败，正在重试")
    def create_lock(self):
        self.lock = site.amc_request(
            [
                {
                    "mode": "page",
                    "wiki_page": self.unix_name,
                    "force_lock": "yes",
                    "moduleName": "edit/PageEditModule",
                }
            ]
        )[0].json()

    def __init__(self, title: str, unix_name: str, source: str, tags: str):
        match unix_name:
            case "synergy":
                unix_name = "synergies"
            case "pickup":
                unix_name = "pickups"
            case "achievement":
                unix_name = "achievements"
        self.unix_name, self.title, self.source, self.tags = (
            unix_name,
            title,
            source,
            tags,
        )
        if (pagedata := site.page.get(unix_name, False)) is None:
            self.create_lock()
            self.create_new_page()
            self.id = site.page.get(unix_name).id
        else:
            logger.info(f"{unix_name} 已存在")
            repeat_patt = re.compile(r"[\r\n]|[ \n]$|( \n)")

            if repeat_patt.sub("", pagedata.source.wiki_text) != repeat_patt.sub(
                "", source
            ):
                self.title = pagedata.title
                self.id = pagedata.id
                self.create_lock()
                self.create_new_page(ifEdit=True)
            else:
                logger.info(f"{unix_name} 内容相同，跳过修改")
                self.id = pagedata.id
                self.edit_tags()
                return
        self.edit_tags()


def to_unix(string: str) -> str:
    """
    Converts string to unix name

    Params:
        string: str - String to convert

    Example:
        >>> to_unix("Ammo Box")
        "ammo-box"
    """
    return re.sub(r"[,.'!&\-\\/\(\)\+ ]+", "-", string.lower()).strip("-")


class Generator:
    def add_args(self, key: str, item: dict[str, str], label: str) -> str:
        return (
            (percent.sub("-", "\n" + f"| {label} = {self.to_wikidot(str(value))}"))
            if (value := item.get(key, "")) != ""
            else ""
        )

    def add_link(self, file: str, unix_name: str) -> None:
        if file not in self.links:
            self.links[file] = []
        self.links[file].append(unix_name)

    def create_div_class(self, name: str, element: str | None) -> str:
        if element is None:
            return ""

        return (
            f'[[div_ class="{name}"]]\n'
            + self.to_wikidot(element, False)
            + "\n[[/div]]\n"
        )

    def create_infobox(self) -> str:
        target, locale, add_args = self.target, self.locale, self.add_args

        return (
            "[[include component:infobox"
            + add_args("name", locale if "name" in locale else target, "title")
            + (f"\n| en-title = {target["name"]}" if "name" in locale else "")
            + add_args("icon" if "icon" in target else "local_icon", target, "img")
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
            + add_args(
                "base_health",
                locale,
                "bosshealth" if self.file_name == "boss" else "health",
            )
            + add_args("dps_cap", locale, "dps_cap")
            + "\n]]\n"
        )

    def create_synergy(self, synergy: str, component: bool = False) -> str:
        """
        Creates synergy part for anypage

        Params:
            synergy: str - Name of synergy
            component: bool (optional, False by default) - If it is used for a component page
        """
        target: dict = data_dic["synergy"][synergy]
        add_args = self.add_args
        crafts = ""
        for index, items in enumerate(target.get("group", [])):
            text = f"\n| craft{index + 1} = "
            for item in items:
                file = item["type"].lower()
                name = item["name"]
                unix_name = to_unix(name)
                item_target = data_dic[file][name]
                self.add_link(file, unix_name)
                text += f'[[a href="{"/" if component else "#u-"}{unix_name}"]]'
                if "icon" in item_target:
                    text += f'[[image {IMG_SERVER}/{item_target["icon"]}]][[/a]] '
                elif "local_icon" in item_target:
                    text += f'[[image {IMG_SERVER}/{item_target["local_icon"]}]][[/a]] '
                else:
                    text += f'{item_target["locale"].get("name", item_target["name"])}[[/a]]'
                text = percent.sub("-", text)
                text = text.replace("-.", ".")
                text = re.sub(r"(\/)\-", r"\1", text)
            crafts += text
        return (
            f"[[include component:{"preview-" if component else ""}synergy"
            + (f"\n| unix = {to_unix(synergy)}" if component else "")
            + add_args(
                "name",
                target["locale"] if "name" in target["locale"] else target,
                "title",
            )
            + (f"\n| en-title = {target["name"]}" if "name" in target["locale"] else "")
            + crafts
            + add_args("sprite", target, "result")
            + f"\n| tips = {self.to_wikidot(target["locale"].get("tips"), component)}"
            "\n]]\n"
        )

    def to_wikidot(self, text: str | None, synergy: bool = True) -> str:
        if text is None or text == "":
            return ""

        def replace(old, new):
            nonlocal text
            text = text.replace(old, new)

        def sub(patt, repl):
            nonlocal text
            text = re.sub(patt, repl, text)

        replace("<br/>", "\n")
        replace("\n- ", "\n* ")
        sub(r"(\r\n)+", "\n")
        replace("}}{{", "}} {{")

        for string in re.findall(r"<h\d>.*?</h\d>", text):
            num = int(string[2])

            text = text.replace(string, f"{'+'*num} {string[4:-5]}")

        for string in re.findall(r"\[\((.*?)\)\]", text):
            if string[0] == "#":
                repl = f'[[image {IMG_SERVER}/{string[(2 if string[1] == "~" else 1):]}_c.gif class="media"]]'
            elif string[0] == "!":
                repl = f'[[image {IMG_SERVER}/{"" if string[1] == "~" else "data/"}{string[(2 if string[1] == "~" else 1):]} class="icon"]]'
            elif string[0:2] == "~~":
                repl = f'[[image {IMG_SERVER}/{string[2:]} class="icon"]]'
            elif string[0] == "~":
                repl = f"[[image {IMG_SERVER}/{string[1:]}]]"
            else:
                repl = f"[({string})]"
            replace(f"[({string})]", repl)

        """
        Replace "{foo}" to "**foo**"
        """
        sub(r"(?<!\{)\{([^{]*?)\}", r"**\1**")

        """
        Replace "((foo))" to "{{foo}}"
        """
        sub(r"\(\((.*?)\)\)", r"{{\1}}")

        patt = re.compile(r"\[(\[(\".*?\",?)+\],?)+\]")
        for string in patt.finditer(text):
            data = eval(string.group())
            repl = "\n"
            for line in data:
                for unit in line:
                    if unit and unit[0] == "~":
                        unit = "~ " + unit[1:]
                    unit = unit.replace("\n", " _\n").replace("\n- ", "\n* ")
                    repl += f"||{unit}"
                repl += "||\n"
            text = patt.sub(repl, text, 1)
        replace("||||", "|| ||")

        for string in re.findall(r"\{\{(.*?)\}\}", text):
            if len(groups := re.split(r":", string)) != 2:
                continue

            file = groups[0].lower()
            data = data_dic[file][groups[1]]
            name = data["locale"].get("name", data["name"])

            unix_name = to_unix(groups[1])
            if string == "ENEMY:Shotgrub":
                unix_name = "shotgrub-enemy"
            if string == "BOSS:Resourceful Rat":
                unix_name = "resourceful-rat-boss"
            if string == "BOSS:Blockner":
                unix_name = "blockner-boss"
            if string == "NPC:Winchester":
                unix_name = "winchester-npc"
            if string == "NPC:Grey Mauser":
                unix_name = "grey-mauser-npc"
            if string == "SHRINE:Junk":
                unix_name = "junk-shrine"
            if string == "SHRINE:Beholster":
                unix_name = "beholster-shrine"
            if string == "SHRINE:Companion":
                unix_name = "companion-shrine"
            if string == "SYSTEM:Pickup":
                unix_name = "pickups"
            if string == "SYSTEM:Brick of Cash":
                unix_name = "brick-of-cash-system"
            if string == "SYSTEM:Bullet Kin":
                unix_name = "bullet-kin-system"

            if groups[0] == "QUALITY":
                repl = f"[[image {IMG_SERVER}/{data['local_icon']}]]"
            else:
                if synergy:
                    repl = f'[[a href="/{"pickups#" if groups[0] == "PICKUP" else ""}{unix_name}"'
                else:
                    repl = f'[[a href="#u-{unix_name}"'
                if "icon" in data:
                    repl_part = f"]][[image {IMG_SERVER}/{data["icon"]}]][[/a]]"
                elif "local_icon" in data:
                    repl_part = f"]][[image {IMG_SERVER}/{data["local_icon"]}]][[/a]]"
                else:
                    repl_part = f' class="{"synergy" if groups[0] == "SYNERGY" else "link"}"]]{name}[[/a]]'
                repl += repl_part
                self.add_link(file, unix_name)

            text = text.replace("{{" + string + "}}", repl)

        text = percent.sub("-", text)
        replace("-.", ".")

        """
        Replace "/-" in image links to "/"
        """
        sub(r"(\/)\-", r"\1")

        """
        Replace "<view foo>bar</view>" to "[[span foo]]bar[[/span]]"
        """
        sub(r"<view([^>]*?)>", r"[[span \1]]")

        """
        Replace "- " to "* "
        """
        sub(r"(\| \w+ = )\- ", r"\1* ")

        patt = re.compile(r"<span(.*?)>")
        for string in patt.findall(text):
            text = patt.sub(f"[[span{string.replace("'", "\"")}]]", text, 1)
        replace("<g>", '[[span class="group"]]')
        sub(r"</(g|span|view)>", "[[/span]]")
        sub(r"\]\] ?\n|\]\] ?$", "]] _\n")

        sub("<hr/>", "----")
        replace("[[span ]]", "[[span]]")
        sub(r"\n+ _", "\n _")
        replace(" _\n* ", " _\n\n* ")
        replace(" _\n||", "\n||")
        replace("\\n", "\n")

        return text

    def tags_generate(self, types: str | None, quality: str | None) -> str:
        if types is None:
            types = ""
        match self.file_name:
            case "gun":
                tagtype = "枪械"
            case "item":
                tagtype = "道具"
            case "chamber":
                tagtype = "膛室"
            case "chest":
                tagtype = "宝箱"
            case "enemy":
                tagtype = "敌人"
            case "room":
                tagtype = "房间"
            case "game_mode":
                tagtype = "游戏模式"
            case "gungeoneer":
                tagtype = "角色"
            case "page":
                tagtype = "杂项"
            case "pickup":
                tagtype = "掉落物"
            case "shrine":
                tagtype = "雕像"
            case "system":
                tagtype = "系统"
            case other:
                tagtype = other

        if self.target["name"] == "The Breach":
            tagtype = "房间 杂项"

        if quality == "N" or quality is None:
            qualitytag = ""
        else:
            qualitytag = " ".join([f"{tagtype}品质{level}" for level in quality])

        return f"{types} {qualitytag} {tagtype}"

    def __init__(self, target: dict, file_name: str):
        self.target, self.file_name = target, file_name
        self.links: dict[str, list[str]] = {}
        self.locale: dict = self.target["locale"]

    @Retry("@add_one 运行失败，重试中")
    def add_one(self):
        target, locale = self.target, self.locale
        tips = self.to_wikidot(locale.get("notes", locale.get("tips")), False) + "\n"
        infobox = self.create_infobox()
        unlock = self.create_div_class(
            "unlock",
            locale.get("unlock") if "unlock" in locale else target.get("unlock"),
        )
        trivia = self.create_div_class("trivia", locale.get("trivia"))

        synergies = ""
        for synergy in target.get("synergies", []):
            synergies += self.create_synergy(synergy)

        include = ""
        for file in self.links:
            include += f"[[include data:{file}\n"
            for unix_name in Counter(self.links[file]):
                include += f"| {unix_name} = --]\n"
            include += f"]]\n"

        source = include + infobox + tips + synergies + unlock + trivia

        with open("./output.ftml", "at", encoding="utf-8") as output:
            print(source, file=output, end="")

        page_unix_name = to_unix(target["name"])
        if (
            (self.file_name == "enemy" and page_unix_name == "shotgrub")
            or (
                self.file_name == "boss"
                and (
                    page_unix_name == "resourceful-rat" or page_unix_name == "blockner"
                )
            )
            or (
                self.file_name == "npc"
                and (page_unix_name == "winchester" or page_unix_name == "grey-mauser")
            )
            or (
                self.file_name == "shrine"
                and (
                    page_unix_name == "junk"
                    or page_unix_name == "beholster"
                    or page_unix_name == "companion"
                )
            )
            or (
                self.file_name == "system"
                and (
                    page_unix_name == "brick-of-cash" or page_unix_name == "bullet-kin"
                )
            )
        ):
            page_unix_name = f"{page_unix_name}-{self.file_name}"

        create_page(
            target["locale"].get("name", target["name"]),
            page_unix_name,
            source,
            self.tags_generate(
                target["locale"].get("type", ""), target.get("quality", "")
            ),
        )


def add_loop(table: dict, file_name: str, skip_key: str = None):
    with open("./output.ftml", "w", encoding="utf-8") as output:
        print("", file=output, end="")

    skipped = True

    for target in table.values():
        if skip_key != None and target["name"] != skip_key and skipped:
            logger.info(f"{target["name"]} 跳过修改")
            continue
        else:
            skipped = False
        if not skipped:
            Generator(target, file_name).add_one()


if __name__ == "__main__":
    with open("./createrinfo.json", "r", encoding="utf-8") as f:
        createrinfo: dict = json.load(f)

    file = createrinfo["file"]
    key = createrinfo["key"]

    match createrinfo["creater_mode"]:
        case 0:
            """
            添加某文件中的某个键的内容
            """
            Generator(data_dic[file][key], file).add_one()
        case 1:
            """
            从头开始循环添加整个文件中的内容
            """
            add_loop(data_dic[file], file)
        case 2:
            """
            从指定键值开始循环添加整个文件中的内容
            """
            add_loop(data_dic[file], file, key)
