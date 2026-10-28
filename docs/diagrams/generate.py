#!/usr/bin/env python3
"""Generate the homelab network diagram as both draw.io (.drawio) and SVG
from a single layout definition, so the two never drift apart.

    python3 docs/diagrams/generate.py      # writes network.drawio + network.svg

The .drawio file is the editable source (open in https://app.diagrams.net or
draw.io desktop). The SVG/PNG is what the README displays.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).parent
W, H = 1400, 890
FONT = "Helvetica, Arial, sans-serif"

# ---------------------------------------------------------------- palette
C = {
    "ssh": "#1565C0", "https": "#2E7D32", "sql": "#6A1B9A",
    "acme": "#E65100", "net": "#546E7A", "planned": "#9E9E9E",
}
STY = {  # fill, stroke, dashed
    "internet": ("#F5F5F5", "#9E9E9E", False),
    "host":     ("#EEF3FB", "#6C8EBF", False),
    "vmnet":    ("#FFFFFF", "#6C8EBF", True),
    "vm":       ("#E8F5E9", "#2E7D32", False),
    "vm_plan":  ("#FAFAFA", "#9E9E9E", True),
    "ext":      ("#FFF8E1", "#F9A825", False),
    "admin":    ("#E3F2FD", "#1565C0", False),
    "fw":       ("#FFEBEE", "#C62828", False),
    "legend":   ("#FFFFFF", "#BDBDBD", False),
}

# ---------------------------------------------------------------- layout
# zones: (id, x, y, w, h, style, label, label_pos)
zones = [
    ("z_inet", 30, 12, 1340, 153, "internet", "Internet", "top"),
    ("z_host", 30, 215, 1340, 655, "host",
     "Windows host — VMware Workstation · 16 GB RAM · VMnet8 host adapter 192.168.196.1", "top"),
    ("z_vmnet", 340, 375, 1010, 480, "vmnet",
     "VMnet8 (NAT) — 192.168.196.0/24 · static IPs .10–.13 (DHCP range .128–.254)", "bottom"),
]

# nodes: (id, x, y, w, h, style, title, [lines]); a line starting with "~" is planned
nodes = [
    ("duck", 60, 46, 340, 108, "ext", "DuckDNS", [
        "A  git.sitkevin.duckdns.org → 192.168.196.11",
        "(private IP — nothing exposed to the internet)",
        "TXT _acme-challenge (set by acme.sh)"]),
    ("le", 530, 46, 300, 108, "ext", "Let's Encrypt (ACME CA)", [
        "DNS-01: checks the TXT record",
        "issues cert · 90 days · auto-renew"]),
    ("pub", 960, 46, 380, 108, "ext", "Public DNS & package sources", [
        "DNS forwarders 1.1.1.1 · 9.9.9.9 (DNSSEC)",
        "Ubuntu apt · dl.gitea.com · get.acme.sh"]),

    ("admin", 60, 265, 250, 120, "admin", "Admin PC (Windows)", [
        "192.168.196.1",
        "OpenSSH client · ProxyJump bastion",
        "Browser"]),
    ("nat", 1060, 255, 280, 85, "ext", "VMware NAT gateway", [
        "192.168.196.2 · default route"]),

    ("bastion", 370, 420, 300, 150, "vm", "bastion · 192.168.196.10", [
        "BIND9 :53 — zone homelab.internal",
        "recursive for LAN, DNSSEC validation",
        "SSH :22 jump host (key only)",
        "~Ansible controller (Phase 3)"]),
    ("web01", 730, 420, 300, 150, "vm", "web01 · 192.168.196.11", [
        "Nginx :80 → 301 to HTTPS",
        "Nginx :443 · TLS 1.2/1.3 · Let's Encrypt",
        "Gitea 127.0.0.1:3000 (systemd, user git)",
        "acme.sh renewal (root cron)"]),
    ("mon01", 370, 650, 300, 150, "vm_plan", "mon01 · 192.168.196.13", [
        "~Prometheus :9090 (Phase 4)",
        "~Grafana (Phase 4)",
        "~node_exporter on all nodes",
        "~alerts → Telegram / Discord"]),
    ("db01", 730, 650, 300, 150, "vm", "db01 · 192.168.196.12", [
        "PostgreSQL :5432",
        "web01 only · scram-sha-256 · TLS",
        "~OpenLDAP :389/636 (Phase 2, step 5)",
        "~dc=homelab,dc=internal"]),

    ("fw", 1060, 420, 280, 380, "fw", "ufw — default deny incoming", [
        "bastion",
        "   22/tcp  ← 192.168.196.1 (admin)",
        "   53      ← 192.168.196.0/24",
        "",
        "web01",
        "   22/tcp  SSH via bastion",
        "   80, 443/tcp ← LAN",
        "   3000 closed (127.0.0.1 only)",
        "",
        "db01",
        "   22/tcp  SSH via bastion",
        "   5432/tcp ← web01 only",
        "",
        "All nodes: fail2ban,",
        "SSH key-only, no root login"]),

    ("legend", 60, 640, 250, 170, "legend", "Legend", []),
]

# edges: (points, color, dashed, label, (lx, ly, anchor))
edges = [
    ([(310, 305), (880, 305), (880, 420)], C["https"], False,
     "HTTPS :443 — https://git.sitkevin.duckdns.org", (330, 297, "start")),
    ([(310, 355), (440, 355), (440, 420)], C["ssh"], False,
     "SSH :22", (318, 347, "start")),
    ([(670, 470), (730, 470)], C["ssh"], False, "SSH", (700, 462, "middle")),
    ([(670, 545), (700, 545), (700, 730), (730, 730)], C["ssh"], False, None, None),
    ([(470, 570), (470, 650)], C["ssh"], False, None, None),
    ([(810, 570), (810, 650)], C["sql"], False,
     "SQL :5432 · TLS", (803, 614, "end")),
    ([(960, 570), (960, 650)], C["planned"], True,
     "LDAP (planned)", (966, 614, "start")),
    ([(670, 770), (730, 770)], C["planned"], True, None, None),
    ([(990, 420), (990, 185), (230, 185), (230, 154)], C["acme"], False,
     "DNS-01: acme.sh sets TXT via DuckDNS API (outbound through NAT)", (240, 202, "start")),
    ([(530, 99), (400, 99)], C["acme"], False, "checks TXT", (465, 92, "middle")),
    ([(1200, 255), (1200, 154)], C["net"], False, "outbound NAT", (1208, 207, "start")),
]

# legend content (drawn relative to legend box)
legend_items = [
    (C["https"], False, "HTTPS (users)"),
    (C["ssh"], False, "SSH (admin / ProxyJump)"),
    (C["sql"], False, "Database"),
    (C["acme"], False, "Certificates / DNS-01"),
    (C["planned"], True, "Planned (later phase)"),
]

TITLE_FS, LINE_FS, LINE_H = 15, 12.5, 19


# ================================================================ SVG
def svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="{FONT}">',
         '<defs>']
    for name, col in C.items():
        o.append(f'<marker id="a_{name}" viewBox="0 0 10 10" refX="9" refY="5" '
                 f'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
                 f'<path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>')
    o.append('</defs>')
    o.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

    def box(x, y, w, h, style, rx=10):
        f, s, d = STY[style]
        dash = ' stroke-dasharray="8 5"' if d else ""
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                 f'fill="{f}" stroke="{s}" stroke-width="1.6"{dash}/>')

    for zid, x, y, w, h, st, label, pos in zones:
        box(x, y, w, h, st, 14)
        ly = y + 24 if pos == "top" else y + h - 12
        o.append(f'<text x="{x+14}" y="{ly}" font-size="14" font-weight="bold" '
                 f'fill="{STY[st][1]}">{escape(label)}</text>')

    for nid, x, y, w, h, st, title, lines in nodes:
        box(x, y, w, h, st)
        tcol = "#757575" if st == "vm_plan" else "#212121"
        o.append(f'<text x="{x+14}" y="{y+26}" font-size="{TITLE_FS}" '
                 f'font-weight="bold" fill="{tcol}">{escape(title)}</text>')
        if lines:
            o.append(f'<line x1="{x+14}" y1="{y+36}" x2="{x+w-14}" y2="{y+36}" '
                     f'stroke="{STY[st][1]}" stroke-opacity="0.5"/>')
        for i, ln in enumerate(lines):
            planned = ln.startswith("~")
            txt = ln[1:] if planned else ln
            mono = nid == "fw"
            style = (' fill="#9E9E9E" font-style="italic"' if planned
                     else ' fill="#37474F"')
            fam = ' font-family="Menlo, Consolas, monospace" xml:space="preserve"' if mono else ""
            bold = ' font-weight="bold"' if mono and not txt.startswith(" ") and txt else ""
            fs = 11.5 if mono else LINE_FS
            o.append(f'<text x="{x+14}" y="{y+58+i*LINE_H}" font-size="{fs}"'
                     f'{style}{fam}{bold}>{escape(txt)}</text>')

    def line(pts, col, dashed, name):
        d = " ".join(f"{x},{y}" for x, y in pts)
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        o.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="2"'
                 f'{dash} marker-end="url(#a_{name})"/>')

    names = {v: k for k, v in C.items()}
    for pts, col, dashed, label, lp in edges:
        line(pts, col, dashed, names[col])
        if label:
            lx, ly, anc = lp
            o.append(f'<text x="{lx}" y="{ly}" font-size="12" font-weight="bold" '
                     f'text-anchor="{anc}" fill="{col}" paint-order="stroke" '
                     f'stroke="#FFFFFF" stroke-width="4">{escape(label)}</text>')

    lx, ly = 60, 640
    for i, (col, dashed, text) in enumerate(legend_items):
        y = ly + 55 + i * 22
        line([(lx + 14, y), (lx + 54, y)], col, dashed, names[col])
        o.append(f'<text x="{lx+64}" y="{y+4}" font-size="12" fill="#37474F">'
                 f'{escape(text)}</text>')
    o.append('</svg>')
    return "\n".join(o)


# ================================================================ draw.io
def drawio():
    cells, n = [], [0]

    def nid():
        n[0] += 1
        return f"c{n[0]}"

    def style_box(st, rx=True):
        f, s, d = STY[st]
        return (f"rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor={f};"
                f"strokeColor={s};strokeWidth=1.6;{'dashed=1;' if d else ''}"
                f"align=left;verticalAlign=top;spacingLeft=10;spacingTop=4;"
                f"fontFamily=Helvetica;")

    def vertex(x, y, w, h, value, style, cid=None):
        cid = cid or nid()
        cells.append(f'<mxCell id="{cid}" value="{escape(value)}" style="{style}" '
                     f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" '
                     f'width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    for zid, x, y, w, h, st, label, pos in zones:
        sty = style_box(st).replace("verticalAlign=top", "verticalAlign=" +
                                    ("top" if pos == "top" else "bottom"))
        sty += f"fontStyle=1;fontSize=14;fontColor={STY[st][1]};spacingBottom=4;"
        vertex(x, y, w, h, label, sty, zid)

    boxes = {}
    for key, x, y, w, h, st, title, lines in nodes:
        boxes[key] = (x, y, w, h)
        parts = [f"<b style='font-size:{TITLE_FS}px'>{escape(title)}</b>"]
        if lines:
            parts.append("<hr style='margin:4px 0'>")
        body = []
        for ln in lines:
            if ln.startswith("~"):
                body.append(f"<i><font color='#9E9E9E'>{escape(ln[1:])}</font></i>")
            elif key == "fw" and ln and not ln.startswith(" "):
                body.append(f"<b>{escape(ln)}</b>")
            else:
                body.append(escape(ln).replace(" ", "&nbsp;") if key == "fw" else escape(ln))
        parts.append("<br>".join(body))
        sty = style_box(st) + f"fontSize={LINE_FS};fontColor=#37474F;"
        if key == "fw":
            sty += "fontFamily=Courier New;"
        vertex(x, y, w, h, "".join(parts), sty, key)

    def find_box(px, py):
        for key, (x, y, w, h) in boxes.items():
            if x - 1 <= px <= x + w + 1 and y - 1 <= py <= y + h + 1:
                return key, (px - x) / w, (py - y) / h
        return None, None, None

    def edge(pts, col, dashed, value=""):
        src, sx, sy = find_box(*pts[0])
        tgt, tx, ty = find_box(*pts[-1])
        sty = (f"edgeStyle=none;html=1;rounded=0;endArrow=block;endFill=1;"
               f"strokeColor={col};strokeWidth=2;{'dashed=1;' if dashed else ''}")
        attrs = ""
        if src:
            sty += f"exitX={sx:.4f};exitY={sy:.4f};exitDx=0;exitDy=0;"
            attrs += f' source="{src}"'
        if tgt:
            sty += f"entryX={tx:.4f};entryY={ty:.4f};entryDx=0;entryDy=0;"
            attrs += f' target="{tgt}"'
        way = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pts[1:-1])
        geo = (f'<mxGeometry relative="1" as="geometry">'
               f'<mxPoint x="{pts[0][0]}" y="{pts[0][1]}" as="sourcePoint"/>'
               f'<mxPoint x="{pts[-1][0]}" y="{pts[-1][1]}" as="targetPoint"/>'
               + (f'<Array as="points">{way}</Array>' if way else "") + '</mxGeometry>')
        cells.append(f'<mxCell id="{nid()}" value="{escape(value)}" style="{sty}" '
                     f'edge="1" parent="1"{attrs}>{geo}</mxCell>')

    def label(text, x, y, anchor, col):
        w = int(len(text) * 7.2) + 10
        lx = {"start": x - 4, "middle": x - w / 2, "end": x - w + 4}[anchor]
        align = {"start": "left", "middle": "center", "end": "right"}[anchor]
        vertex(lx, y - 14, w, 18, text,
               f"text;html=1;align={align};verticalAlign=middle;fontSize=12;"
               f"fontStyle=1;fontColor={col};labelBackgroundColor=#FFFFFF;")

    for pts, col, dashed, text, lp in edges:
        edge(pts, col, dashed)
        if text:
            label(text, lp[0], lp[1], lp[2], col)

    lx, ly = 60, 640
    for i, (col, dashed, text) in enumerate(legend_items):
        y = ly + 55 + i * 22
        edge([(lx + 14, y), (lx + 54, y)], col, dashed)
        vertex(lx + 60, y - 9, 180, 18, text,
               "text;html=1;align=left;verticalAlign=middle;fontSize=12;fontColor=#37474F;")

    body = "".join(cells)
    return (f'<mxfile host="generate.py"><diagram id="network" name="Network">'
            f'<mxGraphModel dx="{W}" dy="{H}" grid="1" gridSize="10" guides="1" '
            f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            f'pageWidth="{W}" pageHeight="{H}" math="0" shadow="0"><root>'
            f'<mxCell id="0"/><mxCell id="1" parent="0"/>{body}'
            f'</root></mxGraphModel></diagram></mxfile>\n')


if __name__ == "__main__":
    (OUT / "network.svg").write_text(svg(), encoding="utf-8")
    (OUT / "network.drawio").write_text(drawio(), encoding="utf-8")
    print("wrote", OUT / "network.svg", OUT / "network.drawio")
