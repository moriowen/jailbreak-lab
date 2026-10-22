"""Shared pieces for the HW3 report: print CSS, HTML table helper, matplotlib → inline SVG."""
import html
import io

SID_SLOT = '<span class="sid"></span>'

# Light print palette: categorical slots 1-3 of the reference palette (validated all-pairs).
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"

CSS = """
@page { size: Letter; margin: 0.7in 0.75in; }
:root { color-scheme: light; }
body { font-family: "Helvetica Neue", Arial, sans-serif; font-size: 10pt; line-height: 1.38;
       color: #111; background: #fff; margin: 0; }
h1 { font-size: 15pt; margin: 0 0 4pt; }
h2 { font-size: 12.5pt; margin: 14pt 0 4pt; border-bottom: 1.2pt solid #222; padding-bottom: 2pt;
     break-after: avoid; }
h3 { font-size: 10.5pt; margin: 8pt 0 3pt; break-after: avoid; }
h4 { font-size: 10pt; margin: 6pt 0 2pt; font-style: italic; font-weight: 600; }
p { margin: 0 0 5pt; }
ul, ol { margin: 0 0 5pt 16pt; padding: 0; }
li { margin: 0 0 2pt; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.6pt; }
table { border-collapse: collapse; width: 100%; margin: 3pt 0 6pt; font-size: 8.6pt; }
tr { break-inside: avoid; }
th, td { border-bottom: 0.5pt solid #bbb; padding: 2pt 4pt; text-align: left; vertical-align: top; }
th { border-bottom: 1pt solid #333; font-weight: 600; }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
td.n { white-space: nowrap; }
caption { caption-side: top; text-align: left; font-size: 8.6pt; font-weight: 600; padding-bottom: 2pt; }
blockquote { margin: 2pt 0 5pt 0; padding: 3pt 7pt; border-left: 2.5pt solid #888; background: #f4f4f2;
             font-family: Menlo, Consolas, monospace; font-size: 8.4pt; white-space: pre-wrap; }
figure { margin: 4pt 0 8pt; break-inside: avoid; }
blockquote { break-inside: avoid; }
figcaption { font-size: 8.6pt; color: #333; margin-top: 2pt; }
.cover { border: 1pt solid #222; padding: 8pt 10pt; margin-bottom: 8pt; }
.cover p { margin: 0 0 2pt; }
.glance { background: #f4f4f2; border-left: 3pt solid #222; padding: 6pt 9pt; margin: 6pt 0 8pt; }
.wrong { color: #b00000; }
.small { font-size: 8.6pt; color: #333; }
.term { font-family: Menlo, Consolas, monospace; font-size: 7.2pt; line-height: 1.32; background: #101418;
        color: #d6dde6; padding: 6pt 8pt; white-space: pre; overflow: hidden; margin: 0; }
.win { border-radius: 5pt; overflow: hidden; break-inside: avoid; margin: 4pt 0 8pt; border: 0.6pt solid #2b323a; }
.wbar { background: #2b323a; color: #c9d1da; font: 7.4pt Menlo, Consolas, monospace; padding: 3pt 7pt; display: flex;
        align-items: center; gap: 4pt; }
.wbar i { width: 6pt; height: 6pt; border-radius: 50%; background: #5d6670; display: inline-block; }
.wbar span { margin-left: 4pt; }
ul.rounds { margin: 0 0 4pt 14pt; font-size: 8.8pt; }
ul.rounds li { margin: 0; }
.term .hl { color: #7fd1ff; }
.pb { break-before: page; }
.q { break-before: auto; }
table.keep { break-inside: avoid; }
table.gloss { font-size: 7.8pt; margin: 0; }
table.gloss td:first-child { white-space: nowrap; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 10pt; }
"""


def esc(s):
    return html.escape(str(s), quote=False)


def table(head, rows, caption=None, num_cols=(), cls=""):
    """HTML table. num_cols: indices of right-aligned numeric columns."""
    h = "".join(f'<th class="{"n" if i in num_cols else ""}">{c}</th>' for i, c in enumerate(head))
    body = "".join(
        "<tr>" + "".join(f'<td class="{"n" if i in num_cols else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>"
        for r in rows)
    cap = f"<caption>{caption}</caption>" if caption else ""
    return f'<table class="{cls}">{cap}<thead><tr>{h}</tr></thead><tbody>{body}</tbody></table>'


def svg(fig):
    """Matplotlib figure → inline SVG string (text kept as text, so it prints crisply)."""
    import matplotlib.pyplot as plt

    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    plt.close(fig)
    s = buf.getvalue()
    return s[s.index("<svg"):]


def style_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK2)
        ax.spines[side].set_linewidth(0.6)
    ax.tick_params(colors=INK2, labelsize=7, width=0.6, length=2.5)
    ax.yaxis.grid(True, color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def mpl_setup():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"svg.fonttype": "none", "font.family": "Helvetica Neue",
                         "font.size": 7.5, "axes.labelcolor": INK2, "text.color": INK})
    return plt
