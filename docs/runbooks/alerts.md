# Runbook — Responding to alerts

Alerts come from Prometheus (rules: [`homelab-rules.yml`](../../ansible/roles/prometheus/files/homelab-rules.yml)) through Alertmanager to Discord. A **RESOLVED** message follows automatically when the condition clears.

First, look at the situation from the monitoring side:

```bash
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 mon01     # Grafana :3000, Prometheus :9090
```

On the bastion, the lab-wide check gives a quick overview:

```bash
sudo /usr/local/bin/lab-check.sh                                 # DNS, SSH ports, Gitea HTTPS, certificate
ansible homelab -b -m command -a "/usr/local/bin/node-check.sh"  # disk, failed units, memory on every host
```

---

## InstanceDown (critical)

node_exporter on a host hasn't answered for 2 minutes. While it fires, the host's `warning` alerts are suppressed (inhibition).

1. Is the host up? `ping <ip>` from the bastion, VMware console.
2. If it is up: `ansible <host> -b -m command -a "systemctl status prometheus-node-exporter --no-pager"`
3. Firewall: port 9100 must be allowed from mon01 — `ansible <host> -b -m command -a "ufw status numbered"`
4. Fix the drift with Ansible: `ansible-playbook playbooks/monitoring.yml --limit <host>`

## PostgresDown (critical)

`pg_up == 0` — the exporter can't connect. **Gitea is down too.**

1. `ansible db01 -b -m command -a "systemctl status postgresql --no-pager"`
2. `ansible db01 -b -m shell -a "tail -n 50 /var/log/postgresql/postgresql-*-main.log"`
3. Disk full? (`DiskAlmostFull` is suppressed only if db01 itself is down) — `df -h`
4. Data loss → [restore runbook](restore.md), section 3.

## EndpointDown (critical)

The HTTPS probe of Gitea from mon01 fails.

1. `curl -sI https://git.sitkevin.duckdns.org` from the bastion — status code?
2. DNS: `dig +short git.sitkevin.duckdns.org` → must be `192.168.196.11`
3. web01: `systemctl status nginx gitea`, `sudo nginx -t`, `journalctl -u gitea -n 50`
4. Certificate: `echo | openssl s_client -connect git.sitkevin.duckdns.org:443 -servername git.sitkevin.duckdns.org 2>/dev/null | openssl x509 -noout -dates`

## CertificateExpiringSoon (warning)

Less than 14 days left. acme.sh should have renewed ~30 days before expiry, so **automatic renewal is broken**.

1. web01, as root: `crontab -l | grep acme` — the cron job must exist.
2. Renew by hand and read the error: `/root/.acme.sh/acme.sh --renew -d git.sitkevin.duckdns.org --force`
3. Common cause: DuckDNS token changed (DNS-01 can't create the TXT record). Update `vault_duckdns_token` and `/root/.acme.sh/account.conf`.
4. `--reloadcmd` reloads Nginx automatically after a successful renewal.

## DiskAlmostFull (warning)

A filesystem is > 85 % full.

1. Biggest directories: `sudo du -xh / --max-depth=2 2>/dev/null | sort -h | tail -20`
2. Usual suspects: `journalctl --disk-usage` (`sudo journalctl --vacuum-time=14d`), `/var/log`, apt cache (`sudo apt clean`), Prometheus data on mon01 (retention 15 d), restic repositories on mon01 (`restic forget --prune` runs nightly).
3. Long term: grow the VM disk.

## MemoryLow (warning)

< 10 % memory available for 5 minutes.

1. Top consumers: `ps aux --sort=-%mem | head` or the *Node Exporter Full* dashboard (Memory panels).
2. OOM kills so far: `journalctl -k | grep -i oom`

## SystemdUnitFailed (warning)

```bash
ansible <host> -b -m command -a "systemctl --failed --no-pager"
ansible <host> -b -m command -a "journalctl -u <unit> -n 50 --no-pager"
```

Fix the cause and restart the unit. A unit that no longer exists but is still remembered as failed (e.g. after removing a service) is cleared with `systemctl reset-failed <unit>` — see the [2026-10-28 postmortem](../postmortems/2026-10-28-gitea-installed-on-wrong-host.md).

## BackupFailed / BackupTooOld (warning)

```bash
ansible <host> -b -m command -a "journalctl -u homelab-backup -n 30 --no-pager"
ansible <host> -b -m command -a "systemctl list-timers homelab-backup.timer --no-pager"
```

Common causes: mon01 unreachable (SFTP on port 22), repository locked by an interrupted run (`restic unlock`), disk full on mon01. After fixing, run a backup by hand and check that the alert resolves:

```bash
ansible <host> -b -m command -a "systemctl start homelab-backup.service"
```
