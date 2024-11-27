#!/bin/bash

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <state-machine-arn> [region]"
    exit 1
fi

STATE_MACHINE_ARN=$1
REGION=${2:-us-west-2}
TOTAL_STOPPED=0
START_TIME=$(date +%s)
last_log_time=$START_TIME

function stop_batch() {
    local executions=$1
    local count=0
    for execution in $executions; do
        aws stepfunctions stop-execution --execution-arn "$execution" --region "$REGION" &>/dev/null &
        ((count++))
    done
    wait
    echo "$count"
}

function show_progress() {
    local current=$1
    local current_time=$(date +%s)
    if ((current_time - last_log_time >= 10)); then
        local elapsed=$((current_time - START_TIME))
        local rate=$(bc <<< "scale=2; $current / ($elapsed / 60)")
        echo "Progress: $current executions stopped (${rate}/minute)"
        last_log_time=$current_time
    fi
}

echo "Stopping running executions..."
while true; do
    executions=$(aws stepfunctions list-executions \
        --state-machine-arn "$STATE_MACHINE_ARN" \
        --status "RUNNING" \
        --region "$REGION" \
        --max-items 100 \
        --query 'executions[*].executionArn' \
        --output text)
    
    if [ -z "$executions" ]; then
        break
    fi
    
    count=$(stop_batch "$executions")
    TOTAL_STOPPED=$((TOTAL_STOPPED + count))
    show_progress $TOTAL_STOPPED
done

TOTAL_TIME=$(($(date +%s) - START_TIME))
FINAL_RATE=$(bc <<< "scale=2; $TOTAL_STOPPED / ($TOTAL_TIME / 60)")
echo "Complete: $TOTAL_STOPPED executions stopped in ${TOTAL_TIME}s (${FINAL_RATE}/minute)"