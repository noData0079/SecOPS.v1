#!/bin/bash
# tools/ice-age/forensic-replay.sh
# Forensic replay CLI for post-incident analysis

set -e

REPLAY_DIR="${REPLAY_DIR:-./data/episodic_memory}"
OUTPUT_DIR="${OUTPUT_DIR:-./forensic_reports}"

log() {
    echo -e "\033[1;36m[FORENSIC] $1\033[0m"
}

usage() {
    echo "Forensic Replay CLI - Post-incident analysis tool"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  list                    List all recorded incidents"
    echo "  show <incident_id>      Show details of an incident"
    echo "  timeline <incident_id>  Show action timeline"
    echo "  analyze <incident_id>   Run analysis on incident"
    echo "  export <incident_id>    Export incident to JSON"
    echo "  compare <id1> <id2>     Compare two incidents"
    echo ""
}

list_incidents() {
    log "Listing all recorded incidents..."
    echo ""
    printf "%-40s %-20s %-15s %-10s\n" "INCIDENT ID" "TIMESTAMP" "OUTCOME" "ACTIONS"
    echo "--------------------------------------------------------------------------------"
    
    for file in "$REPLAY_DIR"/*.json; do
        if [ -f "$file" ]; then
            incident_id=$(jq -r '.incident_id' "$file" 2>/dev/null || echo "unknown")
            timestamp=$(jq -r '.started_at' "$file" 2>/dev/null || echo "unknown")
            outcome=$(jq -r '.final_outcome' "$file" 2>/dev/null || echo "unknown")
            actions=$(jq -r '.actions_taken' "$file" 2>/dev/null || echo "0")
            printf "%-40s %-20s %-15s %-10s\n" "$incident_id" "${timestamp:0:19}" "$outcome" "$actions"
        fi
    done
}

show_incident() {
    local incident_id="$1"
    local file="$REPLAY_DIR/${incident_id}.json"
    
    if [ ! -f "$file" ]; then
        echo "Incident not found: $incident_id"
        exit 1
    fi
    
    log "Incident Details: $incident_id"
    echo ""
    jq '.' "$file"
}

show_timeline() {
    local incident_id="$1"
    local file="$REPLAY_DIR/${incident_id}.json"
    
    if [ ! -f "$file" ]; then
        echo "Incident not found: $incident_id"
        exit 1
    fi
    
    log "Action Timeline: $incident_id"
    echo ""
    
    jq -r '.episodes[] | "\(.timestamp) | \(.policy_decision) | \(.action_taken.tool // "no-action") | \(.outcome.success // "pending")"' "$file" | while read line; do
        echo "  $line"
    done
}

analyze_incident() {
    local incident_id="$1"
    local file="$REPLAY_DIR/${incident_id}.json"
    
    if [ ! -f "$file" ]; then
        echo "Incident not found: $incident_id"
        exit 1
    fi
    
    log "Analyzing incident: $incident_id"
    echo ""
    
    # Basic stats
    echo "=== SUMMARY ==="
    echo "Started: $(jq -r '.started_at' "$file")"
    echo "Resolved: $(jq -r '.resolved_at // "N/A"' "$file")"
    echo "Outcome: $(jq -r '.final_outcome' "$file")"
    echo "Resolution Time: $(jq -r '.resolution_time_seconds' "$file")s"
    echo ""
    
    echo "=== ACTIONS ==="
    echo "Total Actions: $(jq -r '.actions_taken' "$file")"
    echo "Successful: $(jq -r '.successful_actions' "$file")"
    echo ""
    
    echo "=== TOOL USAGE ==="
    jq -r '[.episodes[].action_taken.tool // empty] | group_by(.) | map({tool: .[0], count: length}) | .[]| "\(.tool): \(.count)"' "$file"
    echo ""
    
    echo "=== POLICY DECISIONS ==="
    jq -r '[.episodes[].policy_decision] | group_by(.) | map({decision: .[0], count: length}) | .[] | "\(.decision): \(.count)"' "$file"
}

export_incident() {
    local incident_id="$1"
    local file="$REPLAY_DIR/${incident_id}.json"
    
    if [ ! -f "$file" ]; then
        echo "Incident not found: $incident_id"
        exit 1
    fi
    
    mkdir -p "$OUTPUT_DIR"
    local output_file="$OUTPUT_DIR/${incident_id}_forensic_$(date +%Y%m%d_%H%M%S).json"
    
    log "Exporting incident to: $output_file"
    
    cp "$file" "$output_file"
    
    # Add metadata
    jq '. + {forensic_export: {exported_at: now | todate, hostname: $hostname}}' \
        --arg hostname "$(hostname)" \
        "$file" > "$output_file"
    
    echo "Export complete: $output_file"
}

# Main
case "${1:-help}" in
    list)
        list_incidents
        ;;
    show)
        show_incident "$2"
        ;;
    timeline)
        show_timeline "$2"
        ;;
    analyze)
        analyze_incident "$2"
        ;;
    export)
        export_incident "$2"
        ;;
    compare)
        log "Comparing ${2} and ${3}..."
        diff <(jq '.' "$REPLAY_DIR/${2}.json") <(jq '.' "$REPLAY_DIR/${3}.json") || true
        ;;
    *)
        usage
        ;;
esac
