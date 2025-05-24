import json
import re
from autoCreater import to_unix

for file_name in ["chest","gungeoneer","enemy","boss","npc"]:
    with open(f"./data/{file_name}.js", "r", encoding="utf-8") as f:
        file: dict = json.loads(
            f.read()[17:]
        )

    squares = []
    for target in file.values():
        name = to_unix(target["name"])
        icon = target.get("icon", target.get("local_icon"))[(len(file_name)+1):-4]
        icon = re.sub(r"%\d+", "-", icon)
        icon = re.sub(r"\.+|(\-\.)", "\.", icon)
        icon = re.sub(r"(\\\.)|-$", "", icon)
        icon = icon.replace("/-", "/")
        squares.append(f"({name}, {icon})")

    source = "@each $name, $pic in "+" ,".join(squares)+" {"

    with open(f"./{file_name}.ftml", "w", encoding="utf-8") as output:
        print(source, file=output, end="")
