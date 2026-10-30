#!/usr/bin/env bash
# restic-backup.sh - back up this host to the restic repository on the backup server.
# Deployed by Ansible (role "backup_client"), started by the systemd timer homelab-backup.timer.
#
#   /etc/restic/env          RESTIC_REPOSITORY, RESTIC_PASSWORD_FILE
#   /etc/restic/backup.conf  BACKUP_PATHS (array), KEEP_*, optional pre_backup() function
#
# Steps: pre_backup (dumps) -> restic backup -> forget/prune (retention) -> restic check
# Result is written for node_exporter's textfile collector, so Prometheus can alert
# when a backup failed or is too old.
#
# Exit codes: 0 = backup OK, non-zero = failed (see journalctl -u homelab-backup)
# Manual run: sudo systemctl start homelab-backup.service
set -euo pipefail
umask 077                                  # dumps contain password hashes

ENV_FILE=${ENV_FILE:-/etc/restic/env}
CONF=${CONF:-/etc/restic/backup.conf}
TEXTFILE_DIR=${TEXTFILE_DIR:-/var/lib/prometheus/node-exporter}
METRICS="$TEXTFILE_DIR/homelab_backup.prom"

# shellcheck source=/dev/null
source "$ENV_FILE"
export RESTIC_REPOSITORY RESTIC_PASSWORD_FILE
# shellcheck source=/dev/null
source "$CONF"

start=$(date +%s)

log() { printf '%s %s\n' "$(date -Is)" "$*"; }   # stdout -> journald

write_metrics() {   # usage: write_metrics EXIT_CODE
    local status=$1 now last_ok tmp
    now=$(date +%s)
    # keep the previous success time when this run failed
    last_ok=$(awk '/^homelab_backup_last_success_timestamp_seconds / {print $2}' "$METRICS" 2>/dev/null || true)
    if (( status == 0 )); then last_ok=$now; fi
    mkdir -p "$TEXTFILE_DIR"
    tmp=$(mktemp "$TEXTFILE_DIR/.homelab_backup.XXXXXX")   # not *.prom -> ignored until renamed
    {
        echo "# HELP homelab_backup_last_status Exit code of the last backup run (0 = OK)."
        echo "# TYPE homelab_backup_last_status gauge"
        echo "homelab_backup_last_status $status"
        echo "# HELP homelab_backup_last_run_timestamp_seconds End of the last backup run."
        echo "# TYPE homelab_backup_last_run_timestamp_seconds gauge"
        echo "homelab_backup_last_run_timestamp_seconds $now"
        echo "# HELP homelab_backup_duration_seconds Duration of the last backup run."
        echo "# TYPE homelab_backup_duration_seconds gauge"
        echo "homelab_backup_duration_seconds $(( now - start ))"
        if [[ -n $last_ok ]]; then
            echo "# HELP homelab_backup_last_success_timestamp_seconds End of the last SUCCESSFUL backup."
            echo "# TYPE homelab_backup_last_success_timestamp_seconds gauge"
            echo "homelab_backup_last_success_timestamp_seconds $last_ok"
        fi
    } > "$tmp"
    chmod 0644 "$tmp"
    mv "$tmp" "$METRICS"                   # atomic: node_exporter never reads half a file
}

on_exit() {
    local rc=$?
    write_metrics "$rc" || true
    if (( rc == 0 )); then log "backup OK in $(( $(date +%s) - start ))s"; else log "backup FAILED (exit $rc)"; fi
    exit "$rc"
}
trap on_exit EXIT

log "backup of ${BACKUP_PATHS[*]} to $RESTIC_REPOSITORY"

if declare -F pre_backup >/dev/null; then
    log "pre_backup: dumps"
    pre_backup
fi

restic backup --tag scheduled --host "$(hostname -s)" "${BACKUP_PATHS[@]}"

log "retention: daily=$KEEP_DAILY weekly=$KEEP_WEEKLY monthly=$KEEP_MONTHLY"
restic forget --tag scheduled --host "$(hostname -s)" \
    --keep-daily "$KEEP_DAILY" --keep-weekly "$KEEP_WEEKLY" --keep-monthly "$KEEP_MONTHLY" --prune

restic check                               # repository structure is consistent
