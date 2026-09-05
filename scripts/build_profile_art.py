#!/usr/bin/env python3
"""Build the animated profile artwork from the original avatar and local data."""

from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "profile"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)

COLORS = ("#39e5dc", "#ff6f91", "#c4f279", "#ffc477")
FOCUSES = (
    ("Agentic coding", ("SWE-Compass / WebCompass", "CodeTracer / Solvita")),
    ("Multi-agent systems", ("AutoMV / Vibe AIGC",)),
    ("Reasoning + alignment", ("HiPO / Inverse IFEval", "KAT-Coder")),
    ("Scientific ideation", ("MotivGraph-SoIQ / MMG2Skill",)),
)


def element(parent, tag, **attributes):
    return ET.SubElement(parent, f"{{{NS}}}{tag}", {
        key.rstrip("_").replace("_", "-"): str(value)
        for key, value in attributes.items()
    })


def text(parent, x, y, value, size=22, color="#eaf3ef", **attributes):
    node = element(parent, "text", x=x, y=y, font_size=size, fill=color, **attributes)
    node.text = value
    return node


def animate(parent, attribute, values, duration="6s", **attributes):
    return element(parent, "animate", attributeName=attribute, values=values,
                   dur=duration, repeatCount="indefinite", **attributes)


def canvas(width, height, title, description):
    root = ET.Element(f"{{{NS}}}svg", {
        "viewBox": f"0 0 {width} {height}", "width": str(width),
        "height": str(height), "fill": "none", "role": "img",
        "aria-labelledby": "title description",
        "font-family": "Arial, Helvetica, sans-serif", "letter-spacing": "0",
    })
    element(root, "title", id="title").text = title
    element(root, "desc", id="description").text = description
    defs = element(root, "defs")
    glow = element(defs, "filter", id="glow", x="-40%", y="-40%", width="180%", height="180%")
    element(glow, "feGaussianBlur", stdDeviation="1.7", result="blur")
    merge = element(glow, "feMerge")
    element(merge, "feMergeNode", in_="blur")
    element(merge, "feMergeNode", in_="SourceGraphic")
    pattern = element(defs, "pattern", id="grid", width=32, height=32, patternUnits="userSpaceOnUse")
    element(pattern, "path", d="M 32 0 H 0 V 32", stroke="#26342f", stroke_width="0.7")
    element(root, "rect", width=width, height=height, fill="#090e0c")
    element(root, "rect", width=width, height=height, fill="url(#grid)", opacity="0.42")
    for index, color in enumerate(COLORS):
        element(root, "rect", x=width * index / 4, y=0, width=width / 4, height=3, fill=color)
    element(root, "path", d=f"M 0 {height - 1} H {width}", stroke="#31463a")
    return root


def signal(parent, path, color, duration="5s", begin="0s"):
    element(parent, "path", d=path, stroke=color, stroke_width="1.5", opacity="0.3")
    packet = element(parent, "rect", x=-3, y=-3, width=6, height=6, fill=color, filter="url(#glow)")
    element(packet, "animateMotion", path=path, dur=duration, begin=begin, repeatCount="indefinite")


def nameplate(parent, x, y, size, width):
    text(parent, x, y, "Xinping Lei", size, font_weight="bold")
    clip = element(parent.find(f"{{{NS}}}defs"), "clipPath", id="name-scan")
    slit = element(clip, "rect", x=x - 5, y=y - size, width=width, height=8)
    animate(slit, "y", f"{y - size};{y + 5};{y + 5}", "5s", keyTimes="0;0.55;1")
    overlay = element(parent, "g", clip_path="url(#name-scan)", aria_hidden="true")
    text(overlay, x + 2, y, "Xinping Lei", size, COLORS[0], font_weight="bold", filter="url(#glow)")
    text(overlay, x - 2, y, "Xinping Lei", size, "none", stroke=COLORS[1], stroke_width="1", font_weight="bold")


def avatar(parent, transform):
    source = ET.parse(ROOT / "assets" / "banner.svg").getroot()
    group = source.find(f"{{{NS}}}g[@transform='translate(15,-8) scale(0.84)']")
    if group is None:
        raise ValueError("The original banner avatar could not be found")
    group = deepcopy(group)
    group.set("transform", transform)
    replacements = {
        "url(#g1)": COLORS[0], "url(#fg)": "url(#glow)",
        "url(#fs)": "url(#glow)", "#a855f7": COLORS[3],
        "#ff00e5": COLORS[1], "#00f0ff": COLORS[0],
    }
    for node in group.iter():
        for key, value in list(node.attrib.items()):
            node.set(key, replacements.get(value, value))
    parent.append(group)


def banner(mobile=False):
    width, height = (420, 540) if mobile else (1120, 430)
    root = canvas(width, height, "Xinping Lei | Research Lab",
                  "An animated portrait of Xinping Lei with moving circuit signals. LLM agents, agentic coding, and research engineering.")
    mono = {"font_family": "'Courier New', monospace"}
    text(root, 26 if mobile else 32, 34, "bupterlxp / research.lab", 17, COLORS[0], **mono)
    if mobile:
        nameplate(root, 26, 94, 49, 350)
        text(root, 28, 129, "LLM agents + agentic coding", 22, COLORS[0])
        avatar(root, "translate(66,112) scale(0.72)")
        signal(root, "M 26 172 V 394 H 52", COLORS[0], "5s")
        signal(root, "M 394 172 V 394 H 368", COLORS[1], "6s")
        text(root, 210, 466, "RESEARCH / BUILD / EVALUATE", 20, COLORS[2], text_anchor="middle", **mono)
        text(root, 210, 505, "one idea, many possibilities.", 18, "#a6b7af", text_anchor="middle", **mono)
    else:
        text(root, 1088, 34, "AGENTS / CODE / IDEAS", 17, "#a6b7af", text_anchor="end", **mono)
        avatar(root, "translate(38,39) scale(0.78)")
        nameplate(root, 354, 159, 80, 570)
        element(root, "path", d="M 357 181 H 574", stroke=COLORS[0], stroke_width=3)
        element(root, "path", d="M 581 181 H 639", stroke=COLORS[1], stroke_width=3)
        text(root, 358, 222, "LLM AGENTS + AGENTIC CODING", 25, COLORS[0])
        text(root, 358, 261, "Research, systems, and the tools in between.", 24, "#a6b7af")
        text(root, 358, 336, "> research / build / evaluate / repeat", 22, COLORS[2], **mono)
        cursor = element(root, "rect", x=866, y=320, width=12, height=20, fill=COLORS[2])
        animate(cursor, "opacity", "1;1;0;0;1", "1.6s")
        signal(root, "M 982 80 H 1044 V 293 H 990 V 359 H 938", COLORS[1], "7s")
        signal(root, "M 956 80 H 1018 V 271 H 964 V 335 H 924", COLORS[0], "5s")
        text(root, 32, 408, "NATIVE CURIOSITY", 15, "#a6b7af", **mono)
        text(root, 1088, 408, "one idea, many possibilities.", 16, "#a6b7af", text_anchor="end", **mono)
    return root


def research(mobile=False):
    width, height = (420, 642) if mobile else (1120, 458)
    root = canvas(width, height, "Research Constellation",
                  "Four connected research directions: agentic coding, multi-agent systems, reasoning and alignment, and scientific ideation.")
    text(root, 26 if mobile else 32, 43, "RESEARCH CONSTELLATION", 20, COLORS[0], font_family="'Courier New', monospace")
    if mobile:
        for index, ((title, papers), color) in enumerate(zip(FOCUSES, COLORS)):
            y = 98 + 132 * index
            if index < 3:
                signal(root, f"M 40 {y + 8} V {y + 124}", color, f"{3 + index}s")
            element(root, "rect", x=34, y=y - 7, width=12, height=12, fill=color)
            text(root, 62, y + 3, title, 23, color, font_weight="bold")
            for row, value in enumerate(papers):
                lines = value.split(" / ") if len(value) > 24 else [value]
                for line, label in enumerate(lines):
                    text(root, 62, y + 37 + row * 50 + line * 24, label, 20, "#cad8d0")
        text(root, 26, 614, "questions > experiments > evidence", 17, "#a6b7af", font_family="'Courier New', monospace")
    else:
        for index, ((title, papers), color) in enumerate(zip(FOCUSES, COLORS)):
            right = index % 2
            bottom = index // 2
            x, y = (750 if right else 40), (322 if bottom else 125)
            end = 720 if right else 388
            path = f"M 560 230 H {end} V {y - 7} H {x - 20 if right else x + 322}"
            signal(root, path, color, f"{4 + index}s", f"-{index}s")
            text(root, x, y, title, 26, color, font_weight="bold")
            for row, value in enumerate(papers):
                text(root, x, y + 36 + row * 29, value, 22, "#cad8d0")
        element(root, "path", d="M 560 168 L 622 230 L 560 292 L 498 230 Z", fill="#101b14", stroke=COLORS[0], stroke_width=2)
        trace = element(root, "path", d="M 560 156 L 634 230 L 560 304 L 486 230 Z", stroke=COLORS[1], stroke_width=2, stroke_dasharray="16 20", filter="url(#glow)")
        animate(trace, "stroke-dashoffset", "0;-144", "12s")
        text(root, 560, 225, "LEI", 27, font_weight="bold", text_anchor="middle")
        text(root, 560, 251, "LAB", 19, COLORS[0], text_anchor="middle")
        text(root, 1088, 432, "questions > experiments > evidence", 17, "#a6b7af", text_anchor="end", font_family="'Courier New', monospace")
    return root


def terminal(mobile=False):
    width, height = (420, 290) if mobile else (1120, 198)
    root = canvas(width, height, "The Research Loop",
                  "An animated illustration of the research loop: ask, build, evaluate, and iterate.")
    mono = {"font_family": "'Courier New', monospace"}
    text(root, 26 if mobile else 32, 39, "~/research $ run --curiosity", 18, COLORS[0], **mono)
    labels = ("ASK", "BUILD", "EVALUATE", "ITERATE")
    for index, (label, color) in enumerate(zip(labels, COLORS)):
        x = 26 + (index % 2) * 195 if mobile else 32 + index * 274
        y = 99 + (index // 2) * 84 if mobile else 103
        text(root, x, y, label, 23, color, font_weight="bold", **mono)
        element(root, "path", d=f"M {x} {y + 19} h {158 if mobile else 218}", stroke="#34473c", stroke_width=3)
        pulse = element(root, "path", d=f"M {x} {y + 19} h {158 if mobile else 218}", stroke=color, stroke_width=3, stroke_dasharray="28 230")
        animate(pulse, "stroke-dashoffset", "258;0", "4s", begin=f"-{index}s")
    text(root, 26 if mobile else 32, height - 26, "while curious: keep_building()", 18, "#a6b7af", **mono)
    return root


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, render in (("banner", banner), ("research", research), ("terminal", terminal)):
        for mobile in (False, True):
            path = OUTPUT / f"{name}{'-mobile' if mobile else ''}.svg"
            root = render(mobile)
            ET.indent(root, space="  ")
            ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
            print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
