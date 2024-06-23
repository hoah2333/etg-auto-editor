from autoCreater import *

filename = "gun"

with open(f"./data/{filename}.js", "r", encoding="utf-8") as f:
    file: dict = json.loads(f.read()[17:])

text = ""

for target in file.values():
    locale = target["locale"]
    unix_name = to_unix(target["name"])
    if filename == "enemy" and unix_name == "shotgrub":
        unix_name = "shotgrub-enemy"
    if filename == "boss" and unix_name == "resourceful-rat":
        unix_name = "resourceful-rat-boss"
    if filename == "boss" and unix_name == "blockner":
        unix_name = "blockner-boss"
    generator = Generator(target, "start")
    add_args = generator.add_args
    if filename == "synergy":
        synergy = generator.create_synergy(target["name"], True)
        source = f"[!-- {{${unix_name}}}\n" + synergy + "[!-- --]\n"
    else:
        source = (
            f"[!-- {{${unix_name}}}\n"
            + "[[include component:preview-box"
            + f"\n| unix = {unix_name}"
            + add_args(
                "name",
                locale if "name" in locale else target,
                "title",
            )
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
            + add_args("charge", target, "charge")
            + add_args("shot_speed", target, "shotspeed")
            + add_args("range", target, "range")
            + add_args("force", target, "force")
            + add_args("spread", target, "spread")
            + add_args("sell", target, "sell")
            + add_args(
                "base_health", locale, "bosshealth" if filename == "boss" else "health"
            )
            + add_args("dps_cap", locale, "dps_cap")
            + generator.to_wikidot(add_args("tips", locale, "tips"))
            + "\n]]\n"
            + "[!-- --]\n"
        )

    text += re.sub(r"([\.-])(?=\.[a-z]{3})", "", source)

with open("./output.ftml", "w", encoding="utf-8") as output:
    print(text, file=output, end="")

create_page("", f"data:{filename}", text, "")
