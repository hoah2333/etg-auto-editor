import json
import re


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

with open(f"./data/synergy.js", "r", encoding="utf-8") as f:
    synergy = json.loads(f.read()[17:])

synergy_1 = "[[include :data:synergy-1\n"
synergy_2 = "[[include :data:synergy-2\n"
flag = 1
for target in synergy:
    print(target)
    if target == "Just Like The Real Thing":
        flag = 2
    
    name = to_unix(target)

    if flag == 1:
        synergy_1 += f"| {name} = {{${name}}}\n"
    elif flag == 2:
        synergy_2 += f"| {name} = {{${name}}}\n"

source = synergy_1 + "]]\n" + synergy_2 + "]]\n"

with open("./output.ftml", "w", encoding="utf-8") as output:
    print(source, file=output, end="")
