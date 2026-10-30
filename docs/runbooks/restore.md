# Runbook — Restore from backup (restic)

| | |
|---|---|
| **Applies to** | web01 (Gitea data), db01 (PostgreSQL `gitea`, OpenLDAP) |
| **Backups** | restic repositories on mon01 (`/srv/restic/<host>/repo`), nightly 02:00 / 02:30 |
| **RPO** | up to 24 h (nightly backup) |
| **Last verified** | 2026-10-30 — sections 1–4 (scratch-database restore, LDAP comparison) |

All commands run **as root on the host being restored**. Load the repository settings first:

```bash
sudo -i
set -a; . /etc/restic/env; set +a      # RESTIC_REPOSITORY, RESTIC_PASSWORD_FILE
```

## 1. Check the backups

```bash
restic snapshots                        # list snapshots (time, host, paths, size)
restic check --read-data                # read + decrypt every byte -> "no errors were found"
journalctl -u homelab-backup -n 20      # last run
systemctl list-timers homelab-backup.timer
```

## 2. Restore to a temporary directory (never directly over live data)

```bash
restic restore latest --target /tmp/restore
# one path only:
restic restore latest --target /tmp/restore --include /var/lib/gitea/data/gitea-repositories
# an older snapshot: restic snapshots -> restic restore <ID> --target /tmp/restore
```

Files appear under `/tmp/restore/<original path>`, mode `0600` root.

## 3. PostgreSQL (db01) — verify on a scratch database

```bash
runuser -u postgres -- createdb gitea_restore_test
# root opens the 0600 file and passes it on stdin to pg_restore running as postgres
runuser -u postgres -- pg_restore -d gitea_restore_test < /tmp/restore/var/backups/homelab/gitea.pgdump

for db in gitea gitea_restore_test; do
  runuser -u postgres -- psql -d $db -Atc "SELECT (SELECT count(*) FROM \"user\"), (SELECT count(*) FROM repository), (SELECT count(*) FROM information_schema.tables WHERE table_schema='public')"
done                                    # both lines must be identical

runuser -u postgres -- dropdb gitea_restore_test
```

### Replace the production database (Gitea outage)

```bash
# web01:  sudo systemctl stop gitea
# db01:
runuser -u postgres -- pg_restore --clean --if-exists -d gitea < /tmp/restore/var/backups/homelab/gitea.pgdump
# roles (only if they were lost):  runuser -u postgres -- psql -f /tmp/restore/var/backups/homelab/postgres-globals.sql
# web01:  sudo systemctl start gitea  -> log in, check repositories
```

## 4. OpenLDAP (db01) — compare with the live directory

```bash
diff <(grep -E '^(dn|member):' /tmp/restore/var/backups/homelab/ldap-data.ldif | sort) \
     <(slapcat -n 1 | grep -E '^(dn|member):' | sort) && echo "LDAP identical"
```

### Rebuild the directory from the export (LDAP outage)

```bash
systemctl stop slapd
mv /var/lib/ldap /var/lib/ldap.broken-$(date +%F) && install -d -o openldap -g openldap -m 0700 /var/lib/ldap
sudo -u openldap slapadd -n 1 -F /etc/ldap/slapd.d -l /tmp/restore/var/backups/homelab/ldap-data.ldif
systemctl start slapd
ldapwhoami -x -ZZ -H ldap://db01.homelab.internal -D "uid=binh,ou=people,dc=homelab,dc=internal" -W
```

`ldap-config.ldif` (`cn=config`) is only needed if `/etc/ldap/slapd.d` itself is lost; normally the Ansible role `openldap` recreates the configuration.

## 5. Gitea files (web01)

```bash
systemctl stop gitea
rsync -a --delete /tmp/restore/var/lib/gitea/ /var/lib/gitea/
chown -R git:git /var/lib/gitea
systemctl start gitea
```

Restore the database (section 3) from the **same night** as the files, so repository rows and repository directories match.

## 6. Clean up

```bash
rm -rf /tmp/restore
```

A restored backup only counts once it has been compared with what it should contain (row counts, LDAP entries, a repository cloned) — record the date in **Last verified** above.
