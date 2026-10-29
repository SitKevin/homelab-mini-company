#!/usr/bin/env python3
"""Architecture diagram (icon style). Usage: python3 docs/diagrams/generate_architecture.py docs/diagrams/architecture.svg"""
from html import escape
import sys

W, H = 1600, 1030
F = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"
o = []

# ------------------------------------------------------------------ icons
# simple stroke icons on a 24x24 grid
ICONS = {
    "server": '<rect x="3" y="3" width="18" height="7" rx="2"/><rect x="3" y="14" width="18" height="7" rx="2"/>'
              '<circle cx="7" cy="6.5" r="0.9" fill="currentColor"/><circle cx="7" cy="17.5" r="0.9" fill="currentColor"/>'
              '<path d="M11 6.5h6M11 17.5h6"/>',
    "db": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/>'
          '<path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z"/>',
    "cloud": '<path d="M7 18h10.5a4.5 4.5 0 0 0 .6-8.96A6 6 0 0 0 6.3 10.2 4 4 0 0 0 7 18z"/>',
    "laptop": '<rect x="4" y="5" width="16" height="11" rx="1.5"/><path d="M2 19h20"/>',
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/>'
             '<circle cx="17" cy="9" r="2.5"/><path d="M15.5 14.3c3 .2 5.5 2.6 5.5 5.7"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "key": '<circle cx="7.5" cy="15.5" r="4.5"/><path d="M10.7 12.3 20 3M16 7l3 3M14 9l2 2"/>',
    "shield": '<path d="M12 3 4 6v6c0 4.5 3.4 8.3 8 9 4.6-.7 8-4.5 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    "terminal": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3M12 15h5"/>',
    "branch": '<circle cx="6" cy="5" r="2.2"/><circle cx="6" cy="19" r="2.2"/><circle cx="18" cy="8" r="2.2"/>'
              '<path d="M6 7.2v9.6M18 10.2c0 4-5 3.5-10.5 7.3"/>',
    "cert": '<rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M7 8h7M7 11h4"/>'
            '<circle cx="16" cy="15" r="3"/><path d="m14.5 17.6-.8 3.4 2.3-1.2 2.3 1.2-.8-3.4"/>',
    "dns": '<circle cx="12" cy="5" r="2.5"/><circle cx="5" cy="19" r="2.5"/><circle cx="19" cy="19" r="2.5"/>'
           '<path d="M12 7.5v4M12 11.5 6.5 17M12 11.5l5.5 5.5"/>',
    "proxy": '<path d="M4 7h11M12 4l3 3-3 3"/><path d="M20 17H9M12 14l-3 3 3 3"/>',
    "chart": '<path d="M4 20V4M4 20h16"/><path d="m7 15 4-5 3 3 5-6"/>',
    "gauge": '<path d="M4 17a8 8 0 1 1 16 0"/><path d="m12 17 4-5"/><circle cx="12" cy="17" r="1.2" fill="currentColor"/>',
    "bell": '<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    "gear": '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1"/>',
    "box": '<path d="M3 7.5 12 3l9 4.5v9L12 21l-9-4.5z"/><path d="M3 7.5 12 12l9-4.5M12 12v9"/>',
    "router": '<rect x="3" y="12" width="18" height="7" rx="2"/><path d="M7 15.5h.01M11 15.5h.01"/>'
              '<path d="M15 12V8M9.5 6a5 5 0 0 1 11 0"/>',
    "folder": '<path d="M3 6.5A1.5 1.5 0 0 1 4.5 5H9l2 2.5h8.5A1.5 1.5 0 0 1 21 9v9.5a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18.5z"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
}


def icon(name, x, y, s=24, color="#334155", sw=1.8):
    k = s / 24
    o.append(f'<g transform="translate({x},{y}) scale({k})" fill="none" stroke="{color}" '
             f'stroke-width="{sw/k*k:.2f}" stroke-linecap="round" stroke-linejoin="round" '
             f'color="{color}">{ICONS[name]}</g>')


def text(x, y, s, size=14, color="#0f172a", weight=400, anchor="start", mono=False, italic=False):
    fam = ' font-family="JetBrains Mono, Menlo, Consolas, monospace"' if mono else ""
    it = ' font-style="italic"' if italic else ""
    o.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" '
             f'text-anchor="{anchor}"{fam}{it}>{escape(s)}</text>')


def rect(x, y, w, h, fill, stroke="none", rx=14, sw=1.5, dash=None, filt=None, op=1):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    f_ = f' filter="url(#{filt})"' if filt else ""
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
             f'stroke="{stroke}" stroke-width="{sw}"{d}{f_} opacity="{op}"/>')


def pill(x, y, label, color, bg="#ffffff", ic=None, size=12.5, anchor="middle", border=True):
    w = len(label) * size * 0.58 + 22 + (20 if ic else 0)
    x0 = {"middle": x - w / 2, "start": x, "end": x - w}[anchor]
    rect(x0, y - 13, w, 26, bg, color if border else "none", rx=13, sw=1.4)
    tx = x0 + 11
    if ic:
        icon(ic, tx, y - 8, 16, color, 2)
        tx += 20
    text(tx, y + 4.5, label, size, color, 600)
    return w


def path(d, color, w=2.4, dash=None, arrow=True, op=1):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#m{color[1:]})"' if arrow else ""
    o.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}"{da} '
             f'stroke-linecap="round" stroke-linejoin="round"{m} opacity="{op}"/>')


# ------------------------------------------------------------------ palette
GREEN, BLUE, PURPLE, ORANGE, GRAY, SLATE, RED = (
    "#16a34a", "#2563eb", "#7c3aed", "#ea580c", "#94a3b8", "#475569", "#dc2626")
COLORS = [GREEN, BLUE, PURPLE, ORANGE, GRAY, SLATE]

o.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{F}">')
o.append('<defs>')
o.append('<filter id="sh" x="-10%" y="-10%" width="120%" height="130%">'
         '<feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0f172a" flood-opacity="0.10"/></filter>')
o.append('<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
         '<stop offset="0" stop-color="#f8fafc"/><stop offset="1" stop-color="#eef2f7"/></linearGradient>')
for c in COLORS:
    o.append(f'<marker id="m{c[1:]}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" '
             f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>')
o.append('</defs>')
rect(0, 0, W, H, "url(#bg)", rx=0)

# ------------------------------------------------------------------ header
icon("server", 40, 30, 34, "#0f172a", 2)
text(86, 54, "Mini Company Infrastructure", 26, "#0f172a", 800)
text(88, 78, "Homelab · VMware Workstation · Ubuntu Server 26.04 LTS · 100% open source", 14, "#64748b", 500)
lx = 930
for c, lbl, dash in [(GREEN, "HTTPS", None), (BLUE, "SSH", None), (PURPLE, "Data / Auth", None),
                     (ORANGE, "Certificates", None), (GRAY, "Planned", "6 5")]:
    path(f"M{lx} 52 h28", c, 3, dash, arrow=False)
    text(lx + 36, 57, lbl, 13, "#334155", 600)
    lx += 36 + len(lbl) * 7.6 + 30

# ------------------------------------------------------------------ internet zone
rect(30, 100, W - 60, 165, "#ffffff", "#cbd5e1", rx=18, filt="sh")
icon("cloud", 56, 118, 30, "#64748b")
text(94, 140, "Internet", 17, "#475569", 700)
text(58, 176, "Nothing is exposed", 12.5, "#64748b", 500)
text(58, 194, "inbound — the public", 12.5, "#64748b", 500)
text(58, 212, "DNS name points to", 12.5, "#64748b", 500)
text(58, 230, "a private IP.", 12.5, "#64748b", 500)


def ext_card(x, w, ic, title, lines, color):
    rect(x, 118, w, 128, "#fff7ed" if color == ORANGE else "#f8fafc",
         "#fdba74" if color == ORANGE else "#cbd5e1", rx=14)
    rect(x + 14, 132, 38, 38, color, rx=10, op=0.12)
    icon(ic, x + 21, 139, 24, color, 2)
    text(x + 62, 157, title, 16, "#0f172a", 700)
    for i, ln in enumerate(lines):
        text(x + 16, 194 + i * 20, ln, 12.5, "#475569", 500)


ext_card(680, 370, "globe", "DuckDNS", [
    "git.sitkevin.duckdns.org  →  192.168.196.11",
    "TXT _acme-challenge  (DNS-01)"], ORANGE)
ext_card(250, 400, "cert", "Let's Encrypt", [
    "ACME CA · verifies the TXT record",
    "90-day certs · auto-renewed"], ORANGE)
ext_card(1070, 470, "box", "Public DNS & packages", [
    "Forwarders 1.1.1.1 · 9.9.9.9 (DNSSEC)",
    "Ubuntu apt · dl.gitea.com · get.acme.sh"], SLATE)

# ------------------------------------------------------------------ windows host
rect(30, 300, W - 60, 705, "#f1f5f9", "#94a3b8", rx=20, sw=1.6)
icon("laptop", 52, 316, 26, "#475569")
text(88, 336, "Windows host", 17, "#334155", 700)
text(214, 336, "· VMware Workstation · 16 GB RAM · VMnet8 adapter 192.168.196.1", 13.5, "#64748b", 500)

# NAT gateway badge on the host border
rect(1240, 282, 300, 40, "#ffffff", SLATE, rx=20, sw=1.6, filt="sh")
icon("router", 1254, 290, 24, SLATE, 2)
text(1286, 307, "VMware NAT gateway · 192.168.196.2", 13, "#334155", 700)

# left column: people
def person_card(y, ic, title, lines, color):
    rect(55, y, 255, 130, "#ffffff", "#e2e8f0", rx=16, filt="sh")
    rect(71, y + 16, 44, 44, color, rx=12, op=0.12)
    icon(ic, 79, y + 24, 28, color, 2)
    text(127, y + 45, title, 17, "#0f172a", 700)
    for i, ln in enumerate(lines):
        text(73, y + 84 + i * 20, ln, 12.5, "#475569", 500)


person_card(420, "users", "Employees", ["Browser on the LAN", "Log in with LDAP accounts"], GREEN)
person_card(760, "terminal", "Admin", ["OpenSSH · ProxyJump via bastion", "SSH keys only · from .1"], BLUE)

# VMnet8 network
rect(370, 375, 1170, 610, "#ffffff", "#93c5fd", rx=18, sw=1.6, dash="8 6", op=0.85)
rect(392, 361, 420, 28, "#dbeafe", "#93c5fd", rx=14, sw=1.2)
icon("dns", 402, 366, 18, BLUE, 2)
text(426, 380, "VMnet8 (NAT) · 192.168.196.0/24 · static .10–.13", 13, "#1e40af", 700)

# ------------------------------------------------------------------ VM cards
def vm(x, y, w, h, color, ic, name, ip, role, rows, fw, planned=False):
    stroke = "#cbd5e1" if planned else color
    rect(x, y, w, h, "#fafafa" if planned else "#ffffff", stroke, rx=16, sw=1.6,
         dash="7 5" if planned else None, filt=None if planned else "sh")
    # header
    rect(x + 16, y + 16, 46, 46, GRAY if planned else color, rx=12, op=0.14)
    icon(ic, x + 25, y + 25, 28, GRAY if planned else color, 2)
    text(x + 76, y + 40, name, 20, "#94a3b8" if planned else "#0f172a", 800)
    nw = len(name) * 12.5
    rect(x + 82 + nw, y + 24, 128, 22, "#f1f5f9", rx=11)
    text(x + 82 + nw + 64, y + 40, ip, 12, "#475569", 600, "middle", mono=True)
    text(x + 76, y + 60, role, 13, "#94a3b8" if planned else "#64748b", 500)
    # status badge
    if planned:
        pill(x + w - 20, y + 32, "Phase 4", GRAY, "#f8fafc", "clock", 12, "end")
    else:
        pill(x + w - 20, y + 32, "Running", GREEN, "#f0fdf4", "check", 12, "end")
    # rows
    for i, (ric, rname, rdesc, rplan) in enumerate(rows):
        ry = y + 84 + i * 34
        c = GRAY if (planned or rplan) else color
        icon(ric, x + 22, ry, 20, c, 1.9)
        text(x + 52, ry + 15, rname, 14.5, "#94a3b8" if (planned or rplan) else "#0f172a", 700)
        text(x + 52 + len(rname) * 8.6 + 12, ry + 15, rdesc, 13, "#94a3b8" if (planned or rplan) else "#475569",
             500, italic=rplan)
    # firewall footer
    fy = y + h - 34
    o.append(f'<line x1="{x+16}" y1="{fy-10}" x2="{x+w-16}" y2="{fy-10}" stroke="#e2e8f0"/>')
    icon("shield", x + 22, fy - 3, 18, RED if not planned else GRAY, 1.9)
    text(x + 48, fy + 11, fw, 12.5, "#64748b", 600, mono=True)


vm(410, 410, 510, 250, GREEN, "server", "web01", "192.168.196.11", "Reverse proxy · Git service", [
    ("proxy", "Nginx", ":80 → 301  ·  :443 TLS 1.2/1.3", False),
    ("branch", "Gitea", "127.0.0.1:3000 · systemd · user git", False),
    ("cert", "acme.sh", "Let's Encrypt · auto-renew (cron)", False),
], "ufw  22 ← bastion · 80/443 ← LAN")

vm(1010, 410, 510, 250, PURPLE, "db", "db01", "192.168.196.12", "Database · Directory", [
    ("db", "PostgreSQL", ":5432 · scram-sha-256 · TLS", False),
    ("key", "OpenLDAP", ":389 · StartTLS required", False),
    ("folder", "Directory", "people · groups · services", False),
], "ufw  5432, 389 ← web01 only")

vm(410, 740, 510, 230, BLUE, "server", "bastion", "192.168.196.10", "Jump host · DNS · automation", [
    ("dns", "BIND9", ":53 · homelab.internal · DNSSEC", False),
    ("terminal", "SSH", "jump host · key only", False),
    ("gear", "Ansible", "controller — Phase 3", True),
], "ufw  22 ← admin · 53 ← LAN")

vm(1010, 740, 510, 230, GRAY, "server", "mon01", "192.168.196.13", "Monitoring & alerting", [
    ("chart", "Prometheus", ":9090 · node_exporter", True),
    ("gauge", "Grafana", "dashboards", True),
    ("bell", "Alerts", "Telegram / Discord · cert expiry", True),
], "ufw  22 ← bastion", planned=True)

# ------------------------------------------------------------------ connections
# employees -> web01
path("M310 485 H404", GREEN, 2.6)
pill(357, 455, "HTTPS 443", GREEN, "#ffffff", "lock", 12)
# admin -> bastion
path("M310 825 H404", BLUE, 2.6)
pill(357, 795, "SSH 22", BLUE, "#ffffff", "terminal", 12)
# bastion -> web01 (ProxyJump)
path("M560 740 V666", BLUE, 2.2)
pill(560, 700, "ProxyJump", BLUE, "#ffffff", None, 11.5)
# bastion -> mon01
path("M920 870 H1004", BLUE, 2.2)
# bastion -> db01
path("M920 770 H965 V700 H1180 V666", BLUE, 2.2)
pill(1080, 700, "SSH", BLUE, "#ffffff", None, 11.5)
# web01 -> db01 : SQL + LDAP
path("M920 490 H1004", PURPLE, 2.6)
pill(962, 476, "SQL · TLS", PURPLE, "#ffffff", None, 11.5)
path("M920 560 H1004", PURPLE, 2.6)
pill(962, 546, "LDAP · StartTLS", PURPLE, "#ffffff", None, 11.5)
# mon01 -> db01 (planned scrape)
path("M1400 740 V666", GRAY, 2.2, "6 5")
pill(1400, 700, "metrics", GRAY, "#ffffff", None, 11.5)
# web01 -> DuckDNS (DNS-01)
path("M860 410 V252", ORANGE, 2.6)
pill(860, 285, "DNS-01 · TXT via API", ORANGE, "#ffffff", "key", 12)
# LE -> DuckDNS
path("M650 182 H674", ORANGE, 2.4)
# NAT -> public
path("M1390 282 V252", SLATE, 2.4)

# footer note
icon("shield", 58, 918, 20, RED, 1.9)
text(86, 933, "All nodes", 13.5, "#334155", 700)
for i, ln in enumerate(["ufw default-deny", "fail2ban", "SSH key-only · no root login"]):
    text(60, 956 + i * 18, "· " + ln, 12.5, "#475569", 500)

o.append('</svg>')
open(sys.argv[1] if len(sys.argv) > 1 else "architecture.svg", "w").write("\n".join(o))
