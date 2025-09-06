#!/bin/bash

echo '=== Gepett System Status ==='
echo "Timestamp: $(date)"

# Check processes
echo -e '\n--- Processes ---'
ps aux | grep -E '(python|node|java)' | grep -v grep || echo 'No Gepett processes found'

# Check ports
echo -e '\n--- Network Ports ---'
netstat -tlnp 2>/dev/null | grep -E '(25565|5555|5556)' || echo 'No Gepett ports listening'

# Check logs
echo -e '\n--- Recent Logs ---'
find . -name '*.log' -exec tail -5 {} \; 2>/dev/null | head -20 || echo 'No log files found'

echo -e '\n=== End Status ==='
