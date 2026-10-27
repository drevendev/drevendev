"""Explicit authoring operation. Scheduled refresh never calls this script."""
import argparse
import html
from pathlib import Path
import sys

from refresh_profile import ROOT, START, END, ProfileError, block_bounds, load_config


def esc(text):
    return html.escape(text, quote=True)


def link(url, text):
    return f'<a href="{esc(url)}">{esc(text)}</a>'


def render(config, live):
    projects = sorted(config["projects"], key=lambda p: p["stable_display_order"])
    featured = [p for p in projects if p["featured"]]
    cards = []
    for p in featured:
        ctas = " · ".join(link(c["url"], c["label"]) for c in p["ctas"])
        cards.append(f'<h3>{esc(p["label"])}</h3>\n<p><strong>{esc(p["one_liner"])}</strong></p>\n'
                     f'<p>{esc(p["description"])}</p>\n<p>{ctas}</p>')
    if config["layout"] == "grid":
        machinery = '<table>\n<tr>\n' + '\n</tr>\n<tr>\n'.join(
            '\n'.join(f'<td width="50%" valign="top">\n{card}\n</td>' for card in cards[i:i + 2])
            for i in (0, 2)) + '\n</tr>\n</table>'
    else:
        machinery = "\n\n<hr>\n\n".join(cards)
    shelf = "\n".join(f'<li><strong>{link(p["url"], p["label"])}</strong> — {esc(p["description"])}</li>'
                      for p in projects if p["secondary"])
    links = config["links"]
    socials = " &nbsp;·&nbsp; ".join(link(links[k], name) for k, name in
                                    (("linkedin", "LinkedIn"), ("itch", "itch.io"),
                                     ("play", "Google Play"), ("spotify", "Spotify")))
    return f'''<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/header-dark.svg">
  <img src="assets/header-light.svg" alt="Dreven's workshop: small mechanisms for tools, curious systems, simulations and games." width="100%">
</picture>

<div align="center">

<h1>{esc(config["heading"])}</h1>
<p>{esc(config["subtitle"])}</p>
<p><em>{esc(config["character"])}</em></p>

<p>{socials}</p>

</div>

## The main machinery

{machinery}

## From the workbench

Stable public releases, one per project. Release dates are shown in UTC.

<!-- LIVE_RELEASES:START -->{live}<!-- LIVE_RELEASES:END -->

## More from the workshop

<ul>
{shelf}
</ul>

## And when the code starts making noises

Sometimes I make games. Sometimes music. Sometimes the distinction gets blurry.

{link(links["itch"], "Games on itch.io")} · {link(links["play"], "Google Play")}<br>
{link(links["spotify"], "Dr. Weeb")} · {link(links["robot_anime"], "Robot Anime")}

---

<sub>Still making things. Occasionally putting the tools away.</sub>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = ROOT / "README.md"
    try:
        before = path.read_bytes()
        start, end = block_bounds(before)
        output = render(load_config(), before[start:end].decode("utf-8")).encode("utf-8")
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

