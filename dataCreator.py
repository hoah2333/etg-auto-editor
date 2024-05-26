from autoCreater import *

with open("./data/system.js", "r", encoding="utf-8") as f:
    file: dict = json.loads(f.read()[17:])

text=""

for target in file.values():
    locale = target["locale"]
    unix_name = to_unix(target["name"])
    source = ("[!-- {$" + unix_name + "}\n"
    "[[include component:preview-box"
    + add_args("name", locale, "title")
    + f"\n| en-title = {target["name"]}"
    + f"\n| unix = {unix_name}"
    + note(add_args("tips", locale, "tips"))
    + "\n]]\n"
    "[!-- --]\n")

    text+=re.sub(r"([\.-])(?=\.[a-z]{3})", "", source)

with open("./output.ftml", "w", encoding="utf-8") as output:
    print(text, file=output, end="")