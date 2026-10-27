"""Explicit authoring operation. Scheduled refresh never calls this script."""
import argparse
import html
from pathlib import Path
import sys

from refresh_profile import ROOT, START, END, ProfileError, block_bounds, load_config
import build_assets


def esc(text):
    return html.escape(text, quote=True)


def link(url, text):
    return f'<a href="{esc(url)}">{esc(text)}</a>'


def badge(url, asset, label):
    return f'<a href="{esc(url)}"><img src="assets/links/{asset}.svg" width="136" height="38" alt="{esc(label)}"></a>'


def render(config, live):
    projects = sorted(config["projects"], key=lambda p: p["stable_display_order"])
    featured = [p for p in projects if p["featured"]]
    cards = []
    for p in featured:
        ctas = " · ".join(link(c["url"], c["label"]) for c in p["ctas"])
        cards.append(f'<h3>{esc(p["label"])}</h3>\n<p><strong>{esc(p["one_liner"])}</strong></p>\n'
                     f'<p>{esc(p["description"])}</p>\n<p>{ctas}</p>')
    if config["layout"] == "cards":
        visuals = []
        for p in featured:
            ctas = " · ".join(link(c["url"], c["label"]) for c in p["ctas"])
            icon = p.get("icon", "package")
            visuals.append('<table align="left" width="400">\n<tr>'
                           f'<td width="400" height="240" valign="top">'
                           f'<h3><a href="{esc(p["url"])}"><img src="assets/icons/{icon}.svg" width="28" height="28" alt=""> {esc(p["label"])}</a></h3>'
                           f'<p><strong>{esc(p["one_liner"])}</strong></p>'
                           f'<p>{esc(p["description"])}</p>'
                           f'</td></tr>\n<tr><td>{ctas}</td></tr>\n</table>')
        machinery = '\n\n'.join(visuals) + '\n\n<br clear="all">'
    elif config["layout"] == "grid":
        machinery = '<table>\n<tr>\n' + '\n</tr>\n<tr>\n'.join(
            '\n'.join(f'<td width="50%" valign="top">\n{card}\n</td>' for card in cards[i:i + 2])
            for i in (0, 2)) + '\n</tr>\n</table>'
    else:
        machinery = "\n\n<hr>\n\n".join(cards)
    shelf = "\n".join(f'<li><strong>{link(p["url"], p["label"])}</strong> — {esc(p["description"])}</li>'
                      for p in projects if p["secondary"])
    links = config["links"]
    socials = "\n ".join(badge(links[k], k, name) for k, name in
                                    (("linkedin", "LinkedIn"), ("itch", "itch.io"),
                                     ("play", "Google Play"), ("spotify", "Spotify")))
    return f'''<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/header-ecg-dark.svg?v=2">
  <img src="assets/header-ecg-light.svg?v=2" alt="Dreven: crab for tools, ECG pulse line for systems, fireworks for experiments, and scales for simulations." width="100%">
</picture>

<div align="center">

<h1>{esc(config["heading"])}</h1>
<p>{esc(config["subtitle"])}</p>
<p>{esc(config["character"])}</p>

<p>{socials}</p>

</div>

## Projects

{machinery}

## Latest releases

Latest stable release from each project, up to four. Dates are in UTC.

<!-- LIVE_RELEASES:START -->{live}<!-- LIVE_RELEASES:END -->

## More projects

<ul>
{shelf}
</ul>

## Games and music

My games are on itch.io and Google Play. I release music as Dr. Weeb and Robot Anime.

<p>{badge(links["itch"], "itch", "Games on itch.io")} {badge(links["play"], "play", "Google Play")}<br>
{badge(links["spotify"], "dr-weeb", "Dr. Weeb")} {badge(links["robot_anime"], "robot-anime", "Robot Anime")}</p>

---

<sub>Emoji artwork: <a href="docs/ASSET_CREDITS.md">Twemoji · CC BY 4.0</a>.</sub>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = ROOT / "README.md"
    try:
        config = load_config()
        build_assets.build(config, check=args.check)
        before = path.read_bytes()
        start, end = block_bounds(before)
        output = render(config, before[start:end].decode("utf-8")).encode("utf-8")
        if args.check:
            if output != before:
                print("Static README differs from data/profile.json; run python scripts/build_static.py")
                return 1
        elif output != before:
            path.write_bytes(output)
        return 0
    except (OSError, ProfileError) as exc:
        print(str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())

