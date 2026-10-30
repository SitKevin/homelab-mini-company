#!/usr/bin/env bash
# node-check.sh - local health check of ONE server: disk, failed units, memory.
# Deployed by Ansible (role "maintenance") to /usr/local/bin, run by cron every 15 min.
#
# Exit codes: 0 = all OK, 1 = at least one warning
# Log:        /var/log/homelab/node-check.log  (+ syslog, tag "node-check", warnings only)
# Manual run: sudo /usr/local/bin/node-check.sh
set -euo pipefail

LOG_DIR=${LOG_DIR:-/var/log/homelab}
LOG_FILE="$LOG_DIR/node-check.log"
DISK_WARN_PCT=${DISK_WARN_PCT:-80}   # warn when a filesystem is >= this % full
MEM_WARN_MB=${MEM_WARN_MB:-100}      # warn when available memory is below this
TAG=node-check
warnings=0

log() {   # usage: log LEVEL message...
    local level=$1
    shift
    printf '%s %s %-4s %s\n' "$(date -Is)" "$(hostname -s)" "$level" "$*" | tee -a "$LOG_FILE"
    if [[ $level != OK ]]; then
        logger -t "$TAG" -p user.warning -- "$level $*" || true
    fi
}

warn() {
    log WARN "$@"
    warnings=$((warnings + 1))
}

mkdir -p "$LOG_DIR"

# 1. Disk usage of real filesystems (skip tmpfs, snaps, overlays)
while read -r pct mount; do
    pct=${pct%\%}
    if (( pct >= DISK_WARN_PCT )); then
        warn "disk $mount is ${pct}% full (threshold ${DISK_WARN_PCT}%)"
    fi
done < <(df --output=pcent,target -x tmpfs -x devtmpfs -x squashfs -x overlay | tail -n +2)

# 2. systemd units in "failed" state
#    (if systemctl itself fails, that is a warning too - never skip silently)
if ! units=$(systemctl list-units --state=failed --no-legend --plain 2>&1); then
    warn "cannot query systemd: ${units//$'\n'/ }"
else
    mapfile -t failed < <(awk 'NF {print $1}' <<< "$units")
    if (( ${#failed[@]} > 0 )); then
        warn "failed systemd units: ${failed[*]}"
    fi
fi

# 3. Available memory (MemAvailable already counts reclaimable cache)
avail_mb=$(awk '/^MemAvailable:/ {print int($2 / 1024)}' /proc/meminfo)
if (( avail_mb < MEM_WARN_MB )); then
    warn "only ${avail_mb}MB memory available (threshold ${MEM_WARN_MB}MB)"
fi

if (( warnings == 0 )); then
    log OK "disk, units and memory fine (${avail_mb}MB available)"
    exit 0
fi
exit 1
