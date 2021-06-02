import os
import re
from argparse import ArgumentParser
from dataclasses import dataclass

from loguru import logger
from utils.csv import save_dicts
from utils.file import read_lines
from utils.misc import is_linux


@dataclass
class Translation:
    word: str
    t_word: str = ""
    example: str = ""
    status: str = "NOK"


def __main():
    if not is_linux():
        raise Exception("Unsupported OS: only supports Linux")

    parser = ArgumentParser(description="Goethe vocabulary convert from PDF to csv")
    parser.add_argument("input", help="input PDF file")
    parser.add_argument("output", help="output CSV file")

    args = parser.parse_args()

    path = args.input
    output = args.output
    os.system(f"pdftotext -layout {path} {output}")

    lines = read_lines(output)
    translations = []

    re_line_starts_with_spaces = (
        r"^\s{15,}"  # Means that line contains only description for previous word
    )
    re_long_tab = r"\s{30,}"  # Means that line contains additional on left - german word and on right - additional description
    re_spaces_as_tabs = r"\s{3,}"
    for line in lines:
        if (
            "Goethe-Institut e.V." in line
            or not line.strip()
            or re.search("ONLINE.*GLOSSARY.*CHAPTERS", line)
        ):
            continue
        line = line.rstrip()

        cols = re.split(re_spaces_as_tabs, line.strip())

        if re.match(re_line_starts_with_spaces, line) and translations:
            line = re.sub(re_line_starts_with_spaces, " ", line)

            translations[-1].example += line
        elif re.search(re_long_tab, line) and len(cols) == 2 and translations:
            word, example = cols
            translations[-1].word += " " + word
            translations[-1].example += " " + example
        else:
            if len(cols) == 3:
                cols.append("OK")
                translations.append(Translation(*cols))
            elif len(cols) == 2:
                word, example = cols
                translations.append(Translation(word, example=example))
            elif len(cols) == 1 and translations:
                word = cols[0]
                translations[-1].word += " " + word
            else:
                logger.warning(f"failed to parse: {line}")

    good_translations = [t for t in translations if t.status == "OK"]
    bad_translations = [t for t in translations if t.status == "NOK"]
    logger.debug(
        f"Good: {len(good_translations)}, bad: {len(bad_translations)}, total: {len(translations)}"
    )
    save_dicts(output, [t.__dict__ for t in translations], delimiter=";")
    logger.info(f"Saved file {output}")


if __name__ == "__main__":
    __main()
