# Phase 2 — Services (build log)

> Status: ✅ **complete** — PostgreSQL, Gitea, Nginx, Let's Encrypt SSL, OpenLDAP with StartTLS, Gitea LDAP login.

## Target architecture

```
User ──HTTPS 443──> web01 (.11)  Nginx ──> Gitea 127.0.0.1:3000
                                              │
                                              ├──SQL/TLS──> db01 (.12) PostgreSQL :5432 (web01 only)
                                              └──LDAP/StartTLS──> db01 (.12) OpenLDAP :389 (web01 only)
```

| Component  | Host  | Listens on              | Reachable from          |
|------------|-------|-------------------------|-------------------------|
| PostgreSQL | db01  | 127.0.0.1, .12 : 5432   | web01 only (ufw + pg_hba) |
| Gitea      | web01 | 127.0.0.1 : 3000        | localhost only (Nginx)  |
| Nginx      | web01 | 0.0.0.0 : 80, 443       | everyone in the LAN     |
| OpenLDAP   | db01  | 0.0.0.0 : 389 (StartTLS required) | web01 only (ufw) |

**Why Gitea?** Lightweight (~200–300 MB RAM, fits a 1.5 GB VM; GitLab needs ~4 GB), single Go binary, built-in LDAP support, and it will host this project's own Ansible code in Phase 3.

**Public URL:** `https://git.sitkevin.duckdns.org` — a DuckDNS record that points to the **private** IP `192.168.196.11`. Nothing is exposed to the internet; the name just resolves the same way for every machine in the lab (DuckDNS also answers wildcards, so `*.sitkevin.duckdns.org` can be used for future services).

---

## Step 1 — PostgreSQL on db01

Config: [`configs/postgresql/`](../configs/postgresql/)

1. `sudo apt install -y postgresql`
2. Create an **empty database + dedicated non-superuser role** → [`create-gitea-db.sql`](../configs/postgresql/create-gitea-db.sql). Gitea creates its own tables on first run.
   *Why:* least privilege — the app never gets the `postgres` superuser.
3. `listen_addresses = 'localhost,192.168.196.12'` → [`postgresql.conf.snippet`](../configs/postgresql/postgresql.conf.snippet)
4. `pg_hba.conf`: only `gitea` → `gitea` from `192.168.196.11/32` with `scram-sha-256` → [`pg_hba.conf.snippet`](../configs/postgresql/pg_hba.conf.snippet)
5. ufw: allow 5432 from web01 only → [`configs/ufw/phase2-rules.sh`](../configs/ufw/phase2-rules.sh)
   *Why two layers (ufw + pg_hba):* defense in depth — a mistake in one layer is still caught by the other.

**Verification**

| Test | Expected | Result |
|------|----------|--------|
| `psql -h 192.168.196.12 -U gitea -d gitea -c '\conninfo'` from **web01** | connects | ✅ TLS 1.3, `Superuser off` |
| `nc -zv -w 3 192.168.196.12 5432` from **bastion** | blocked | ✅ timeout (ufw DROP) |

![listening on private IP](screenshots/stage2/02-postgres-listen-private-ip.png)
![conninfo from web01](screenshots/stage2/03-postgres-conninfo-from-web01-tls.png)
![blocked from bastion](screenshots/stage2/04-postgres-blocked-from-bastion.png)

> **Reading the error tells you which layer blocked you:** `timed out` = dropped by ufw · `no pg_hba.conf entry for host ...` = rejected by PostgreSQL · `connection refused` = nothing listening on that IP/port.

---

## Step 2 — Gitea on web01

Config: [`configs/gitea/`](../configs/gitea/)

1. `apt install git`; system user `git` (`--system --disabled-password`, shell bash for SSH clones).
   *Why:* if Gitea is compromised, the attacker only gets an unprivileged user.
2. Download the binary from `dl.gitea.com` (latest version from `version.json`), **verify `sha256sum -c`**, install to `/usr/local/bin/gitea` (manually installed software lives in `/usr/local`, apt owns `/usr/bin`).
3. Directories: `/var/lib/gitea/{custom,data,log}` → `git:git 750`; `/etc/gitea` → `root:git 770` **only during the web installer**.
4. systemd unit → [`gitea.service`](../configs/gitea/gitea.service) (`Restart=always`, logs in `journalctl -u gitea`).
5. Web installer reached through an **SSH tunnel** instead of opening port 3000:
   ```powershell
   ssh -J sitkevin@192.168.196.10 -L 3000:127.0.0.1:3000 sitkevin@192.168.196.11
   # then browse http://localhost:3000
   ```
   *Why:* whoever reaches the installer first becomes admin — the tunnel limits that to SSH-key holders.
   Settings: PostgreSQL with `SSL=require`, self-registration disabled, sign-in required, admin account created during install.
6. Lock down after install: `/etc/gitea` → `750`, `app.ini` → `640` (it contains the DB password and secret keys). `HTTP_ADDR = 127.0.0.1` → [`app.ini.example`](../configs/gitea/app.ini.example)

**Backup note for Phase 4:** repositories live on **web01 disk** (`/var/lib/gitea/data`), metadata lives in **PostgreSQL on db01** — a backup needs both.

![gitea systemd active](screenshots/stage2/06-gitea-systemd-active.png)
![gitea listening](screenshots/stage2/07-gitea-journal-listen-3000.png)
![app.ini locked down](screenshots/stage2/10-gitea-config-permission-denied.png)
![gitea dashboard](screenshots/stage2/11-gitea-dashboard-admin.png)

---

## Step 3 — Nginx reverse proxy

Config: [`configs/nginx/gitea.conf`](../configs/nginx/gitea.conf)

- `proxy_pass http://127.0.0.1:3000` + `X-Real-IP` / `X-Forwarded-*` headers so Gitea (and fail2ban) see the real client IP.
- `client_max_body_size 512M` (default 1 MB breaks large pushes with HTTP 413).
- ufw: `allow 'Nginx Full'` (80 + 443). Port 3000 stays closed.
- Gitea `ROOT_URL` / `DOMAIN` updated so clone URLs are correct.
- Habit: **always `nginx -t` before `systemctl reload nginx`.**

**Verification (from bastion, not from web01 itself)**

| Test | Expected | Result |
|------|----------|--------|
| `curl -I http://git.sitkevin.duckdns.org` | 200 | ✅ |
| `nc -zv -w 3 192.168.196.11 3000` | blocked | ✅ timeout |

Gitea is now protected by two layers: ufw drops port 3000, and Gitea only binds to 127.0.0.1 anyway.

---

## Step 4 — Let's Encrypt SSL via DNS-01

**Why DNS-01 instead of HTTP-01:** HTTP-01 requires Let's Encrypt to reach `http://<domain>/.well-known/...` from the internet; our VMs sit behind VMware NAT. DNS-01 only requires publishing a TXT record — `acme.sh` does that through the DuckDNS API — so a private server gets a real, publicly trusted certificate.

```bash
sudo -i
curl https://get.acme.sh | sh                         # installs to /root/.acme.sh + renewal cron
/root/.acme.sh/acme.sh --set-default-ca --server letsencrypt   # default CA is ZeroSSL

read -s -p "DuckDNS token: " DuckDNS_Token; echo      # keeps the token out of bash history
export DuckDNS_Token
/root/.acme.sh/acme.sh --issue --dns dns_duckdns -d git.sitkevin.duckdns.org --dnssleep 60

mkdir -p /etc/nginx/ssl
/root/.acme.sh/acme.sh --install-cert -d git.sitkevin.duckdns.org \
  --key-file       /etc/nginx/ssl/git.key \
  --fullchain-file /etc/nginx/ssl/git.fullchain.pem \
  --reloadcmd      "systemctl reload nginx"
chmod 600 /etc/nginx/ssl/git.key
```

- The token is stored by acme.sh in `/root/.acme.sh/account.conf` (root only) for renewals.
- `--install-cert` copies the cert to a stable path and re-runs `--reloadcmd` after every renewal.
- Certificates are valid 90 days; acme.sh renews automatically (~30 days before expiry). Let's Encrypt no longer sends expiry emails → expiry alerting will be done by Prometheus in Phase 4.
- Nginx: HTTP → HTTPS `301`, TLS 1.2/1.3 only, `fullchain` (includes intermediate), `server_tokens off` → [`nginx.conf.snippet`](../configs/nginx/nginx.conf.snippet).

**Verification**

| Test | Expected | Result |
|------|----------|--------|
| `curl -I http://git.sitkevin.duckdns.org` | 301 → https | ✅ |
| `curl -I https://git.sitkevin.duckdns.org` | 200, no cert error | ✅ |
| `openssl s_client ... \| openssl x509 -noout -issuer -dates` | Let's Encrypt, 90 days | ✅ YE1, 2026-10-28 → 2027-01-26 |
| Browser | padlock, no warning | ✅ |

![duckdns](screenshots/stage2/12-duckdns-domain-added.png)
![curl 301 and 200](screenshots/stage2/13-curl-http-301-https-200.png)
![cert issuer](screenshots/stage2/15-cert-issuer-letsencrypt.png)
![browser padlock](screenshots/stage2/14-browser-https-lock.png)

---

## Step 5 — OpenLDAP on db01

Config: [`configs/ldap/`](../configs/ldap/) · VMware snapshot `before-openldap` taken first (rollback plan).

### 5A — Directory structure

1. `sudo apt install slapd ldap-utils` then `sudo dpkg-reconfigure slapd` → domain `homelab.internal` → base DN **`dc=homelab,dc=internal`** (matches the internal DNS zone).
2. OUs `people`, `groups` → [`base.ldif`](../configs/ldap/base.ldif)
3. Employees (`inetOrgPerson`) → [`users.ldif`](../configs/ldap/users.ldif). Passwords set with `ldappasswd` (stored as `{SSHA}` hashes, never in the LDIF files).
4. Groups (`groupOfNames`) → [`groups.ldif`](../configs/ldap/groups.ldif)

```
dc=homelab,dc=internal
├── ou=people    an, binh, chi, dung
├── ou=groups    it (an) · dev (binh, chi) · staff (everyone)
└── ou=services  gitea  ← read-only bind account
```

![reconfigure + base OUs](screenshots/stage2/16-ldap-reconfigure-and-base-ous.png)
![group members + user bind](screenshots/stage2/18-ldap-group-members-and-user-bind.png)

### 5B — Hardening

| Measure | How | Why |
|---|---|---|
| Dedicated bind account | `cn=gitea,ou=services` → [`services.ldif`](../configs/ldap/services.ldif) | Gitea never holds the admin password; if `app.ini` leaks, the attacker only gets read access |
| No anonymous read | [`acl.ldif`](../configs/ldap/acl.ldif): `to * by users read by * none` | Ubuntu's default `to * by * read` exposes the whole staff directory to anyone on the LAN |
| Passwords unreadable | `to attrs=userPassword by self write by anonymous auth by * none` | Even the bind account can't read hashes — they are only usable to authenticate |
| Internal CA + TLS | [`make-ca.sh`](../configs/ldap/make-ca.sh), [`tls.ldif`](../configs/ldap/tls.ldif), CA cert [`homelab-ca.crt`](../configs/ldap/homelab-ca.crt) | `.internal` can't get a Let's Encrypt cert → own CA, cert with SAN `db01.homelab.internal` |
| TLS mandatory | `olcSecurity: tls=1` | A client that forgets StartTLS is rejected instead of sending passwords in clear text |
| Firewall | ufw: 389/tcp from web01 only | Same pattern as PostgreSQL |

> `cn=config` is changed with `sudo ldapmodify -Y EXTERNAL -H ldapi:///` — the local socket authenticates the Linux root user, so no LDAP password is needed and you can't lock yourself out with a bad ACL.

**Verification**

| Test | Expected | Result |
|------|----------|--------|
| Anonymous `ldapsearch -b dc=homelab,dc=internal` | nothing | ✅ `No such object (32)` |
| Bind as `cn=gitea` and search `uid=binh` | uid, mail returned | ✅ |
| Bind as `cn=gitea` and request `userPassword` | not returned | ✅ only `dn:` |
| `ldapwhoami` **without** StartTLS | rejected | ✅ `Confidentiality required (13)` |
| `ldapwhoami -ZZ` (StartTLS) from db01 and **from web01** | success | ✅ |

![service account](screenshots/stage2/19-ldap-gitea-service-account.png)
![ACL](screenshots/stage2/20-ldap-acl-anonymous-blocked.png)
![TLS required](screenshots/stage2/21-ldap-tls-required.png)
![StartTLS from web01](screenshots/stage2/22-ldap-starttls-from-web01.png)

### 5C — Gitea authentication source

All settings: [`configs/ldap/gitea-auth-source.md`](../configs/ldap/gitea-auth-source.md). Key points: **StartTLS** with certificate verification on, user filter `(&(objectClass=inetOrgPerson)(uid=%[1]s))`, only members of **`cn=staff`** may log in, `(uid=an)` is Gitea admin, user synchronization on (users removed from LDAP get deactivated), "empty search result deactivates all users" **off**.

![auth source groups](screenshots/stage2/23-gitea-ldap-auth-source-groups.png)

---

## Step 6 — End-to-end test

Browser → HTTPS → Nginx → Gitea → StartTLS → OpenLDAP → group check → bind as user.

| Test | Expected | Result |
|------|----------|--------|
| `binh` (dev, staff) logs in | success, normal user | ✅ |
| `an` (it, staff) logs in | success, sees **Site Administration** | ✅ |
| `binh` with wrong password | rejected, generic message | ✅ `Username or password is incorrect.` |
| Remove `dung` from `staff` → log in | rejected ("employee leaves") | ⏳ to demo later |

![binh](screenshots/stage2/24-gitea-login-binh-ldap.png)
![an admin](screenshots/stage2/25-gitea-login-an-admin.png)
![wrong password](screenshots/stage2/26-gitea-login-wrong-password.png)

---

## Issues & debugging log

| # | Symptom | Root cause | Fix | Lesson |
|---|---------|------------|-----|--------|
| 1 | `nano /etc/postgresql/16/main/postgresql.conf` opened an **empty** file | Guessed the PostgreSQL version in the path; the installed version is different. nano silently creates a new file | Exit without saving; `sudo -u postgres psql -c 'SHOW config_file;'` | Ask the service for its config path instead of guessing |
| 2 | `ss -tlnp` showed only `127.0.0.1:5432` after editing | `listen_addresses` change not effective (not applied/saved correctly) | Fixed the line, restarted, verified with `SHOW listen_addresses;` | Verify the *running* value, not just the file ([before](screenshots/stage2/01-postgres-listen-localhost-only.png)) |
| 3 | `psql` looked "stuck" / screen full of `~` and `(END)` | Multi-line SQL waits for `;`; `\l` output opened the `less` pager | `;` to finish, `q` to leave the pager, `\pset pager off` | Read the prompt: `=#` ready, `-#` continuation, `'#` open quote |
| 4 | Gitea install commands ran on **db01** | Wrong terminal tab | Full cleanup, redone on web01 | See [postmortem](postmortems/2026-10-28-gitea-installed-on-wrong-host.md) |
| 5 | `systemctl status` OK but `ss` showed nothing on :3000 | Status was taken 35 ms after start; service had not bound yet | Re-check after a few seconds + `journalctl -u gitea` | `status` is a snapshot, the journal is the history |
| 6 | Installer: *"You cannot disable user self-registration without creating an administrator account"* | Registration disabled but no admin defined → nobody could ever log in | Filled in the admin account section | "Optional" admin is only optional when self-registration is open |
| 7 | `ls /etc/gitea` → Permission denied | Expected: dir is `root:git 750`, my user is not in group `git` | `sudo ls -l /etc/gitea` | Proof the lockdown works |
| 8 | `nc` to web01:3000 returned **refused**, not timeout | Test was run **on web01 itself** → loopback traffic bypasses ufw | Re-ran from bastion → timeout | Always test from the client's point of view |
| 9 | `acme.sh: command not found` right after "Install success" | Installer adds an alias to `~/.bashrc`, current shell had not re-read it | Call `/root/.acme.sh/acme.sh` directly (or `source ~/.bashrc`) | Don't `apt install acme.sh` on top — two copies cause confusion |
| 10 | `openssl` not found / `\` broke the command on Windows | cmd has no openssl and no `\` line continuation | Ran it on bastion | Know which shell you're in |
| 11 | Couldn't find *Site Administration* in Gitea | Menu is under the avatar (top right), not the context switcher on the left | Direct URL `/-/admin/auths` | Admin pages have stable URLs — bookmark them |
| 12 | Risk: pasting a block containing `read -s` | When pasted, `read` can consume the next pasted line as its input | Worked this time, verified with `ldapwhoami`; type secret prompts line by line | Verify secrets were really set, don't assume |
