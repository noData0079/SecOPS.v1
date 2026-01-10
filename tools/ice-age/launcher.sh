#!/bin/bash
# ~/full-ice-age-launcher.sh
# Logs everything to ~/full-ice-age.log

LOGFILE="$HOME/full-ice-age.log"
echo "========== Starting Full Ice Age Launcher $(date) ==========" >> $LOGFILE 2>&1

# Run the main build agent script
MAIN_SCRIPT="$HOME/full-ice-age-agent.sh"  # Path to your main Ice Age script

if [ -f "$MAIN_SCRIPT" ]; then
    echo "$(date): Running main Ice Age agent..." >> $LOGFILE
    bash "$MAIN_SCRIPT" >> $LOGFILE 2>&1
else
    echo "$(date): ERROR - main script not found at $MAIN_SCRIPT" >> $LOGFILE
fi

echo "========== Finished Launcher Run $(date) ==========" >> $LOGFILE 2>&1
