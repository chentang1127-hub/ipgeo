#!/bin/bash
# =============================================================================
# Download MaxMind GeoLite2 databases.
#
# Requires a (free) MaxMind license key.  Sign up at https://www.maxmind.com
# Set the key as MAXMIND_KEY env var or pass it as the first argument.
#
# Usage:
#   export MAXMIND_KEY=your_key_here
#   ./scripts/download-db.sh              # downloads to ./data/
#
#   ./scripts/download-db.sh /custom/path  # downloads to /custom/path/
#
# Cron (weekly):
#   0 3 * * 0 /opt/ipgeo/scripts/download-db.sh >> /var/log/ipgeo-db.log 2>&1
# =============================================================================

set -euo pipefail

MAXMIND_KEY="${MAXMIND_KEY:-${1:-}}"
OUT_DIR="${2:-./data}"
BASE_URL="https://download.maxmind.com/app/geoip_download"

if [ -z "$MAXMIND_KEY" ]; then
    echo "ERROR: Set MAXMIND_KEY env var or pass as first argument."
    echo "  Sign up at https://www.maxmind.com/en/geolite2/signup (free)"
    exit 1
fi

mkdir -p "$OUT_DIR"
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

download_edition() {
    local edition_id="$1"
    local edition_name="$2"
    local archive="$TMPDIR/${edition_name}.tar.gz"

    log "Downloading $edition_id ..."
    curl -sS -L --fail-with-body \
        -o "$archive" \
        "${BASE_URL}?edition_id=${edition_id}&license_key=${MAXMIND_KEY}&suffix=tar.gz"

    log "Extracting $edition_name ..."
    tar -xzf "$archive" -C "$TMPDIR"

    # Find the extracted .mmdb file (tar contains a dated directory)
    local mmdb_file
    mmdb_file=$(find "$TMPDIR" -name "${edition_name}*.mmdb" -type f | head -1)

    if [ -z "$mmdb_file" ]; then
        log "ERROR: No .mmdb file found in $edition_name archive"
        return 1
    fi

    # Atomic replacement: write to .new, then rename
    local dest="$OUT_DIR/${edition_name}.mmdb"
    cp "$mmdb_file" "${dest}.new"
    mv "${dest}.new" "$dest"
    log "Updated: $dest ($(stat -f%z "$dest" 2>/dev/null || stat -c%s "$dest") bytes)"
}

download_edition "GeoLite2-City" "GeoLite2-City"
download_edition "GeoLite2-ASN"  "GeoLite2-ASN"

log "Done!  Databases in $OUT_DIR/"
ls -lh "$OUT_DIR"/*.mmdb
