"""Figure export used by summarize.py and make_diagrams.py.

Writes <name>.png (600 dpi, for the manuscript file) and <name>.pdf (vector, fonts embedded).
Set LDT_TIFF=1 to also write <name>.tif at 1200 dpi (LZW), the bitmap format requested by Heliyon/Elsevier
for line art. Only the export changes; the plotted data are identical to those of v0.3.1.
"""
import os


def hsave(fig, path, **kw):
    base = os.path.splitext(path)[0]
    fig.savefig(base + ".png", dpi=600, **kw)
    fig.savefig(base + ".pdf", **kw)
    if os.environ.get("LDT_TIFF") == "1":
        fig.savefig(base + ".tif", dpi=1200, pil_kwargs={"compression": "tiff_lzw"}, **kw)
