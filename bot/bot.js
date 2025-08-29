import mineflayer from 'mineflayer';
import { pathfinder, Movements } from 'mineflayer-pathfinder';
import { GoalBlock } from 'mineflayer-pathfinder/lib/goals.js';
import { zmqBridge } from './zmq_bridge.js';
import config from './config.json' assert { type: 'json' };

// --- Bot Setup ---
let bot;
try {
  bot = mineflayer.createBot({
    host: config.minecraft.host,
    port: config.minecraft.port,
    username: config.minecraft.username,
    version: config.minecraft.version,
    // Disable console logging of bot chat messages to keep stdout clean
    logErrors: true,
    hideErrors: false,
  });

  bot.loadPlugin(pathfinder);
} catch (e) {
  console.error("!!! Failed to create bot. Is the server running? Check config.json.", e);
  process.exit(1);
}

// --- State Gathering ---

/**
 * Gathers the current state of the bot into a StateFrame object.
 * @returns {object | null} The state frame object, or null if bot is not ready.
 */
function getCurrentStateFrame() {
  if (!bot || !bot.entity) return null;

  const position = bot.entity.position;
  return {
    visual: null, // Symbolic-only for now
    position: {
      x: position.x,
      y: position.y,
      z: position.z,
      yaw: bot.entity.yaw,
      pitch: bot.entity.pitch,
    },
    inventory: bot.inventory.items().map(item => ({
      id: item.name,
      count: item.count,
    })),
    // TODO: Implement a more efficient way to get nearby blocks, this is a placeholder
    nearby_blocks: {
        grid_origin: [Math.floor(position.x) - 5, Math.floor(position.y) - 5, Math.floor(position.z) - 5],
        size: [11, 11, 11],
        blocks: [], // Placeholder
    },
    // TODO: Filter entities to relevant ones
    entities: Object.values(bot.entities).map(e => ({
        id: e.id,
        kind: e.name || e.type,
        pos: [e.position.x, e.position.y, e.position.z]
    })),
    metrics: {
      health: bot.health,
      hunger: bot.food,
      time: bot.time.timeOfDay,
      light: bot.lightLevelAt(position),
    },
    // This should be dynamically generated based on bot's capabilities
    available_actions_schema: [
        { name: "move", params: { x: 'float', y: 'float', z: 'float' } },
        { name: "dig", params: { x: 'int', y: 'int', z: 'int' } },
        { name: "place", params: { block_id: 'str', x: 'int', y: 'int', z: 'int', dx: 'int', dy: 'int', dz: 'int' } },
        { name: "jump", params: {} }
    ],
  };
}


// --- Action Handling ---

/**
 * Handles an action request from the Python core.
 * @param {object} request - The action request. e.g., { cmd: "step", action: { name: "move", params: { ... } } }
 * @returns {Promise<object>} A response object. e.g., { ok: true, obs: <StateFrame> }
 */
async function handleActionRequest(request) {
  if (request.cmd !== 'step' || !request.action) {
    throw new Error('Invalid action request format.');
  }

  const { name, params } = request.action;
  console.log(`Executing action: ${name} with params:`, params);

  switch (name) {
    case 'move': {
      const { x, y, z } = params;
      const defaultMove = new Movements(bot);
      bot.pathfinder.setMovements(defaultMove);
      bot.pathfinder.setGoal(new GoalBlock(x, y, z));
      // It's a fire-and-forget for now. A more robust implementation would await goal fulfillment.
      break;
    }
    case 'dig': {
      const { x, y, z } = params;
      const targetBlock = bot.blockAt(new Vec3(x, y, z));
      if (targetBlock) {
        await bot.dig(targetBlock);
      } else {
        throw new Error(`No block at ${x},${y},${z} to dig.`);
      }
      break;
    }
    case 'jump': {
        bot.setControlState('jump', true);
        await bot.waitForTicks(1);
        bot.setControlState('jump', false);
        break;
    }
    // TODO: Implement other primitive actions (place, craft, etc.)
    default:
      throw new Error(`Unknown action name: ${name}`);
  }

  // Wait a moment for the world to update after the action
  await bot.waitForTicks(5);

  return { ok: true, obs: getCurrentStateFrame() };
}


// --- Control Handling ---

/**
 * Handles a control request from the Python core.
 * @param {object} request - The control request. e.g., { cmd: "reset" }
 * @returns {Promise<object>} A response object. e.g., { ok: true, message: "..." }
 */
async function handleControlRequest(request) {
    const { cmd, id } = request;
    console.log(`Executing control command: ${cmd}`);

    switch(cmd) {
        case 'reset':
            // For MVP, a "reset" means killing the bot and letting docker-compose restart it.
            console.log(">>> Received reset command. Bot will restart.");
            await bot.end();
            process.exit(0);
        case 'snap':
            // Bot needs to be an OP to run server commands
            bot.chat(`/snapshot_world ${id}`);
            return { ok: true, message: `Snapshot command sent for id: ${id}` };
        case 'load':
            bot.chat(`/load_world ${id}`); // Assumes a server-side plugin/command
            return { ok: true, message: `Load command sent for id: ${id}` };
        default:
            throw new Error(`Unknown control command: ${cmd}`);
    }
}


// --- Main Bot Logic ---

bot.once('spawn', async () => {
  console.log('>>> Bot has spawned. Initializing ZMQ bridge...');
  await zmqBridge.start();
  console.log('>>> ZMQ bridge started.');

  // Start the state publishing loop
  setInterval(() => {
    const state = getCurrentStateFrame();
    if (state) {
      zmqBridge.publishState(state);
    }
  }, config.options.state_publish_interval_ms);

  // Start listening for commands from the Python core
  zmqBridge.listenForActions(handleActionRequest);
  zmqBridge.listenForControl(handleControlRequest);

  console.log('>>> Gepett Bot is fully operational.');
  bot.chat("Gepett Bot reporting for duty!");
});

bot.on('kicked', (reason) => {
  console.error('!!! Bot was kicked from the server.', reason);
  process.exit(1);
});

bot.on('error', (err) => {
  console.error('!!! Bot encountered an error.', err);
});
