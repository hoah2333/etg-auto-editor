from autoCreater import Generator

with open("input.txt", "r", encoding="utf-8") as f:
    text = f.read()

soource = Generator("","").to_wikidot(text)

with open("./output.ftml", "w", encoding="utf-8") as output:
    print("", file=output, end="")
