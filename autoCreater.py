from collections import Counter
import json
import os
import re
from typing import Callable
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
                    logger.error(error_text)
                    logger.error(e)
                    if ifRaise and i == times - 1:
                        raise e

        return wrapper

    return decorator


class create_page:
    @Retry("创建页面失败，正在重试")
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
                        if ifEdit == False
                        else f"Data corrected by AutoCreater"
                    ),
                }
            ]
        )
        logger.info(
            f"{self.unix_name} 已创建"
            if ifEdit == False
            else f"{self.unix_name} 已修改"
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

    @Retry("")
    def create_lock(self):
        self.lock = site.amc_request(
            [
                {
                    "mode": "page",
                    "wiki_page": self.unix_name,
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
            pagesource = pagedata.source.wiki_text
            if re.sub(r"[\r\n]", "", pagesource) != re.sub(r"[\r\n]", "", source):
                self.title = pagedata.title
                self.id = pagedata.id
                self.create_lock()
                self.create_new_page(ifEdit=True)
            else:
                logger.info("内容相同，跳过修改")
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
    return re.sub(r"[.'!&\-\\/\(\) ]+", "-", string.lower()).strip("-")


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

        return f'[[div_ class="{name}"]]\n' + self.create_tips(element) + "\n[[/div]]\n"

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
            + add_args("unlock", locale, "unlock")
            + "\n]]\n"
        )

    def create_tips(self, text: str | None, synergy: bool = False) -> str:
        if text is None:
            return ""

        return re.sub(
            r"\[/(?=.*?\])",
            "[/" if synergy else "[#u-",
            self.to_wikidot(text),
        ).replace("pickups#", "").replace("#u-span", "/span")

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
                title = item_target["locale"].get("name", item_target["name"])
                self.add_link(file, unix_name)
                text += f"[{"/" if component else "#u-"}{unix_name} {title}] "
            crafts += text

        return (
            f"[[include component:{"preview-" if component else ""}synergy"
            + (f"\n| unix = {to_unix(synergy)}" if component else "")
            + add_args(
                "name", self.locale if "name" in self.locale else target, "title"
            )
            + (f"\n| en-title = {target["name"]}" if "name" in target["locale"] else "")
            + crafts
            + add_args("sprite", target, "result")
            + f"\n| tips = {self.create_tips(target["locale"].get("tips"), component)}"
            "\n]]\n"
        )

    def to_wikidot(self, text: str | None) -> str:
        if text is None:
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
        for string in re.findall(r"\{\{(.*?)\}\}", text):
            if len(groups := re.split(r":", string)) != 2:
                continue

            file = groups[0].lower()
            data = data_dic[file][groups[1]]
            name = data["locale"].get("name", data["name"])

            unix_name = to_unix(groups[1])
            if string == "ENEMY:Shotgrub":
                unix_name = "shotgrub-enemy"

            if groups[0] == "PICKUP":
                repl = f"[/pickups#{unix_name} {name}]"
                self.add_link(file, unix_name)
            elif groups[0] == "QUALITY":
                repl = f"[[image https://7bye.com/hoah/i/etg/{data['local_icon']}]]"
            else:
                repl = f"[/{unix_name} {name}]"
                self.add_link(file, unix_name)

            text = text.replace("{{" + string + "}}", repl)

        sub(r"(\| \w+ = )\- ", r"\1* ")

        for string in re.findall(r"<h\d>.*?</h\d>", text):
            num = int(string[2])

            text = text.replace(string, f"{'+'*num} {string[4:-5]}")

        sub(
            r"\[\(~+(.*?)\)\]",
            r"[[image https://7bye.com/hoah/i/etg/\1]]",
        )
        text = percent.sub("-", text)
        replace("-.", ".")
        sub(r"\{(.*?)\}", r"**\1**")
        sub(r"\(\((.*?)\)\)", r"{{\1}}")

        patt = re.compile(r"\[(\[(\".*?\",?)+\],?)+\]")
        for string in patt.finditer(text):
            data = eval(string.group())
            repl = ""
            for line in data:
                for unit in line:
                    if unit[0] == "~":
                        unit = "~ " + unit[1:]
                    unit = unit.replace("\n", " _\n")
                    repl += f"||{unit}"
                repl += "||\n"
            text = patt.sub(repl, text, 1)
        sub(r"<view(.*?)>(.*?)</view>", r"\[\[span \g<1>\]\]\g<2>\[\[/span\]\]")

        patt = re.compile(r"<span(.*?)>")
        for string in patt.findall(text):
            text = patt.sub(f"[[span{string.replace("'", "\"")}]]", text, 1)
        replace("<g>", '[[span class="group"]]')
        sub(r"</(g|span)>", "[[/span]]")
        sub(r"\]\]$", "]] ")

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
            case other:
                tagtype = other

        if quality == "N" or quality is None:
            qualitytag = ""
        else:
            qualitytag = " ".join([f"{tagtype}品质{level}" for level in quality])

        return f"{types} {qualitytag} {tagtype}"

    def __init__(self, target: dict, file_name: str):
        self.target, self.file_name = target, file_name
        self.links: dict[str, list[str]] = {}
        self.locale: dict = self.target["locale"]

    def add_one(self):
        target, locale = self.target, self.locale
        tips = self.create_tips(locale.get("notes", locale.get("tips"))) + "\n"
        infobox = self.create_infobox()
        unlock = self.create_div_class("unlock", locale.get("unlock"))
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
        if page_unix_name == "shotgrub" and self.file_name == "enemy":
            page_unix_name = "shotgrub-enemy"

        create_page(
            target["locale"].get("name", target["name"]),
            page_unix_name,
            source,
            self.tags_generate(
                target["locale"].get("type", ""), target.get("quality", "")
            ),
        )


def add_loop(table: dict, file_name: str):
    with open("./output.ftml", "w", encoding="utf-8") as output:
        print("", file=output, end="")

    for target in table.values():
        Generator(target, file_name).add_one()


if __name__ == "__main__":
    file = "boss"

    """
    添加某文件中的某个键的内容
    """
    # add_one(data_dic[file]["Bullet King"], file)

    """
    循环添加整个文件中的内容
    """
    Generator(data_dic["npc"]["Bello"], "npc").add_one()
