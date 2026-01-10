#!/bin/bash

# Detect public IP
PUBLIC_IP=$(curl -s https://api.ipify.org)

# Provider Logic
if [ "${DDNS_PROVIDER}" == "duckdns" ]; then
    RESPONSE=$(curl -s "https://www.duckdns.org/update?domains=${DDNS_DOMAIN}&token=${DDNS_TOKEN}&ip=${PUBLIC_IP}")
elif [ "${DDNS_PROVIDER}" == "noip" ]; then
    RESPONSE=$(curl -s "http://dynupdate.no-ip.com/nic/update?hostname=${DDNS_DOMAIN}&myip=${PUBLIC_IP}" --user "${DDNS_TOKEN}")
fi

# Logging
if [[ $RESPONSE == *"OK"* ]] || [[ $RESPONSE == *"moch"* ]] || [[ $RESPONSE == *"good"* ]]; then
    echo "$(date): DDNS updated to $PUBLIC_IP" >> ~/ddns.log
else
    echo "$(date): DDNS update failed. Response: $RESPONSE" >> ~/ddns.log
fi
