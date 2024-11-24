#!/bin/bash

# List all state machines
state_machines=$(aws stepfunctions list-state-machines --query 'stateMachines[*].stateMachineArn' --output text)

for machine in $state_machines; do
    echo "Processing state machine: $machine"
    
    # List all running executions for this state machine
    executions=$(aws stepfunctions list-executions \
        --state-machine-arn "$machine" \
        --status-filter RUNNING \
        --query 'executions[*].executionArn' \
        --output text)
    
    # Stop each running execution
    for execution in $executions; do
        echo "Stopping execution: $execution"
        aws stepfunctions stop-execution \
            --execution-arn "$execution" \
            --error "ManualStop" \
            --cause "Stopped via CLI script"
        
        if [ $? -eq 0 ]; then
            echo "Successfully stopped execution: $execution"
        else
            echo "Failed to stop execution: $execution"
        fi
    done
done

echo "Finished processing all state machines"
