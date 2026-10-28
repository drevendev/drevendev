"""Build local static cards/buttons from the curated profile config. No network."""
import html
from pathlib import Path
import re
import textwrap

from refresh_profile import ROOT, ProfileError

THEME = """<style>
:root { --paper:#F6F4EF; --ink:#24292F; --line:#B7C4B7; --sage:#52735A; --pulse:#52735A; --muted:#526050; }
@media(prefers-color-scheme:dark) {
:root { --paper:#161D24; --ink:#E9E6DD; --line:#3D4C43; --sage:#87A78C; --pulse:#87A78C; --muted:#B9C8BB; }
}
</style>"""


def escape(text):
    return html.escape(text, quote=True)


def icon_art(icon):
    raw = (ROOT / "assets/icons" / f"{icon}.svg").read_text(encoding="utf-8")
    inner = raw[raw.index(">") + 1:raw.rindex("</svg>")]
    return re.sub(r"<(title|style)\b[^>]*>.*?</\1>", "", inner, flags=re.S)


def text_lines(text, width, max_lines):
    result = textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False)
    if len(result) > max_lines:
        raise ProfileError("Card copy is too long; keep the curated description concise")
    return result


def text_block(lines, x, y, size, line_height, weight=400):
    spans = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else line_height}">{escape(line)}</tspan>'
                    for i, line in enumerate(lines))
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}">{spans}</text>'


def card_svg(project, index, theme):
    title = project["label"]
    description = text_lines(project["description"], 36, 4)
    tagline = text_lines(project["one_liner"], 34, 2)
    accent = {"crab": "#BE1931", "pulse": "#63866A", "sparkles": "#D6A55B", "scales": "#D6A55B"}[project["icon"]]
    paper = "#161D24" if theme == "dark" else "#F6F4EF"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 278" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title>
<desc id="desc">{escape(project["one_liner"] + " " + project["description"])}</desc>
<metadata>Emoji artwork: Twemoji v14.0.2, CC BY 4.0; see docs/ASSET_CREDITS.md. Original layout and ECG pulse.</metadata>
{THEME}
<rect x="1" y="1" width="398" height="276" rx="10" fill="var(--paper,{paper})" stroke="var(--line)" stroke-width="1.5"/>
<path d="M2 20v238" stroke="{accent}" stroke-width="4" stroke-linecap="round"/>
<g fill="var(--ink)" font-family="Arial,Helvetica,sans-serif">
<text x="22" y="26" font-size="10" letter-spacing="2" fill="var(--muted)">{index:02d} / OPEN SOURCE</text>
{text_block([title], 22, 62, 25, 30, 700)}
{text_block(tagline, 22, 106, 20, 25, 700)}
{text_block(description, 22, 174, 19, 24)}
</g>
<svg x="328" y="18" width="50" height="50" viewBox="0 0 36 36" stroke="none">{icon_art(project["icon"])}</svg>
</svg>
'''


def badge_svg(label, kind, width=144):
    drawings = {
        "linkedin": '<rect x="12" y="10" width="20" height="20" rx="3" fill="#0A66C2"/><text x="16" y="25" fill="white" font-family="Arial,Helvetica,sans-serif" font-size="15" font-weight="700">in</text>',
        "itch": '<g fill="none" stroke="#D56A70" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 14h11l5 12q0 3-3 2l-5-4h-6l-5 4q-3 1-3-2z"/><path d="M15 20h6m-3-3v6"/><circle cx="26" cy="18" r="1"/><circle cx="29" cy="21" r="1"/></g>',
        "play": '<path d="M15 10l18 10-18 10z" fill="#D6A55B"/><path d="M15 10v20" stroke="var(--sage)" stroke-width="2"/>',
        "shop": '<g fill="none" stroke="#D6A55B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 18h22l-3-7H15zM14 18v12h18V18M22 30v-8h6v8M20 11l-1 7m7-7 1 7"/></g>',
        "music": '<g fill="none" stroke="var(--sage)" stroke-width="2" stroke-linecap="round"><path d="M20 26V12l12-3v14m-12-6 12-3"/><ellipse cx="16.5" cy="27" rx="3.5" ry="2.5" fill="var(--sage)"/><ellipse cx="28.5" cy="24" rx="3.5" ry="2.5" fill="var(--sage)"/></g>',
    }
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 40" role="img" aria-labelledby="title">
<title id="title">{escape(label)}</title>
{THEME}
<rect x="1" y="1" width="{width - 2}" height="38" rx="7" fill="var(--paper)" stroke="var(--line)" stroke-width="1.5"/>
{drawings[kind]}
<text x="42" y="25" fill="var(--ink)" font-family="Arial,Helvetica,sans-serif" font-size="15.5" font-weight="600">{escape(label)}</text>
</svg>
'''


def outputs(config):
    result = {}
    featured = sorted((p for p in config["projects"] if p["featured"]),
                      key=lambda p: p["stable_display_order"])
    for i, project in enumerate(featured, 1):
        for theme in ("light", "dark"):
            result[f"assets/cards/{project['slug']}-{theme}.svg"] = card_svg(project, i, theme)
    for slug, label, kind in (("linkedin", "LinkedIn", "linkedin"), ("itch", "itch.io", "itch"),
                              ("play", "Google Play", "play"), ("spotify", "Spotify", "music"),
                              ("dr-weeb", "Dr. Weeb", "music"), ("robot-anime", "Robot Anime", "music")):
        result[f"assets/links/{slug}.svg"] = badge_svg(label, kind)
    result["assets/links/idle-fantasy-shop.svg"] = badge_svg("Idle Fantasy Shop", "shop", width=208)
    return result


def build(config, check=False):
    for relative, content in outputs(config).items():
        path = ROOT / relative
        expected = content.encode("utf-8")
        if check:
            if not path.exists() or path.read_bytes() != expected:
                raise ProfileError(f"Static asset differs from config: {relative}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_bytes() != expected:
                path.write_bytes(expected)

