# Postmortems

Blameless write-ups of real incidents in the lab: what happened, why, how it was fixed, and what changed so it can't happen again.

| Date | Incident | Detected by | Lesson |
|---|---|---|---|
| 2026-10-28 | [Gitea installed on the wrong host (db01)](2026-10-28-gitea-installed-on-wrong-host.md) | Reading the shell prompt; leftover found 2 days later by `node-check.sh` | Automate with an explicit target host; check `systemctl --failed` after cleanups |
| 2026-10-30 | [Root locked out of OpenLDAP `cn=config` by `olcSecurity: tls=1`](2026-10-30-ldap-cn-config-lockout.md) | Ansible dry run (`--check`) | After tightening security, re-test the administration path, not only the user path |
