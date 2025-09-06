# Quick restart script for Gepett system
# 1. Start Minecraft server
echo 'Starting Minecraft server...'
cd /path/to/minecraft/server && java -Xmx1024M -Xms1024M -jar server.jar nogui &

# 2. Start Gepett core
echo 'Starting Gepett core...'
cd /path/to/gepett/core && python start_agent.py &

# 3. Start Gepett bot
echo 'Starting Gepett bot...'
cd /path/to/gepett/bot && npm start &

echo 'Gepett system starting...'
