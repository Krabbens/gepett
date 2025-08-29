import zmq
import json
import time
import argparse
import yaml

from .schemas import StateFrame, PrimitiveAction, Position, InventoryItem, NearbyBlocks, Entity, Metrics, ActionSchema
from dataclasses import asdict

class MinecraftAdapter:
    """
    Handles ZeroMQ communication between the Python core and the Node.js bot.
    This class acts as the client, connecting to the bot's ZMQ sockets.
    """
    def __init__(self, config):
        self.config = config
        self.context = zmq.Context()

        # Socket to receive state updates from the bot
        self.state_sub_socket = self.context.socket(zmq.SUB)

        # Socket to send actions and receive next state
        self.action_req_socket = self.context.socket(zmq.REQ)

        # Socket to send control commands (reset, load, etc.)
        self.control_req_socket = self.context.socket(zmq.REQ)

        # Set socket timeouts to prevent indefinite blocking
        self.action_req_socket.setsockopt(zmq.RCVTIMEO, 5000) # 5 seconds
        self.control_req_socket.setsockopt(zmq.RCVTIMEO, 10000) # 10 seconds

    def connect(self):
        """Connects all sockets to their respective endpoints."""
        bot_host = self.config['bot']['host']
        self.state_sub_socket.connect(f"tcp://{bot_host}:{self.config['bot']['ports']['state_pub']}")
        self.state_sub_socket.setsockopt_string(zmq.SUBSCRIBE, "state")
        print(f"State SUB socket connected to tcp://{bot_host}:{self.config['bot']['ports']['state_pub']}")

        self.action_req_socket.connect(f"tcp://{bot_host}:{self.config['bot']['ports']['action_req']}")
        print(f"Action REQ socket connected to tcp://{bot_host}:{self.config['bot']['ports']['action_req']}")

        self.control_req_socket.connect(f"tcp://{bot_host}:{self.config['bot']['ports']['control_req']}")
        print(f"Control REQ socket connected to tcp://{bot_host}:{self.config['bot']['ports']['control_req']}")

    def _dict_to_stateframe(self, data: dict) -> StateFrame:
        """Helper to recursively convert a dict to a StateFrame object."""
        data['position'] = Position(**data['position'])
        data['inventory'] = [InventoryItem(**item) for item in data['inventory']]
        data['nearby_blocks'] = NearbyBlocks(**data['nearby_blocks'])
        data['entities'] = [Entity(**entity) for entity in data['entities']]
        data['metrics'] = Metrics(**data['metrics'])
        data['available_actions_schema'] = [ActionSchema(**schema) for schema in data['available_actions_schema']]
        return StateFrame(**data)

    def receive_state(self, block=True) -> Optional[StateFrame]:
        """Receives a single state frame from the bot."""
        try:
            flags = 0 if block else zmq.NOBLOCK
            topic, msg_json = self.state_sub_socket.recv_multipart(flags=flags)
            state_dict = json.loads(msg_json)
            return self._dict_to_stateframe(state_dict)
        except zmq.Again:
            return None # Non-blocking call and no message available

    def step(self, action: PrimitiveAction) -> StateFrame:
        """Sends an action to the bot and waits for the next state as a response."""
        action_dict = {"cmd": "step", "action": asdict(action)}
        self.action_req_socket.send_json(action_dict)

        response_json = self.action_req_socket.recv_json()
        if not response_json.get('ok'):
            raise RuntimeError(f"Bot returned an error on step: {response_json.get('error', 'Unknown error')}")

        return self._dict_to_stateframe(response_json['obs'])

    def control(self, command: dict) -> dict:
        """Sends a control command to the bot (e.g., reset, load)."""
        self.control_req_socket.send_json(command)
        return self.control_req_socket.recv_json()

    def close(self):
        """Closes all ZMQ sockets and terminates the context."""
        self.state_sub_socket.close()
        self.action_req_socket.close()
        self.control_req_socket.close()
        self.context.term()
        print("ZMQ sockets closed.")

def main():
    """Main function for testing the adapter."""
    parser = argparse.ArgumentParser(description="Run Minecraft Adapter Healthcheck.")
    parser.add_argument('--config', type=str, nargs='+', required=True, help="Path to one or more config files.")
    args = parser.parse_args()

    # Load and merge configs
    config = {}
    for config_path in args.config:
        with open(config_path, 'r') as f:
            config.update(yaml.safe_load(f))

    adapter = None
    try:
        adapter = MinecraftAdapter(config['adapter'])
        adapter.connect()

        print("\n--- Adapter Healthcheck ---")

        # 1. Test receiving state
        print("\n1. Waiting for first state update (max 10s)...")
        state = adapter.receive_state(block=True)
        if state:
            print("   ✅ Received state successfully. Bot position:", state.position)
        else:
            print("   ❌ Failed to receive state.")
            return

        # 2. Test sending a control command (harmless)
        print("\n2. Sending a test control command...")
        response = adapter.control({"cmd": "ping"}) # Assume bot handles 'ping' gracefully
        print(f"   ✅ Received control response: {response}")

        # 3. Test sending an action
        print("\n3. Sending a primitive action (jump)...")
        jump_action = PrimitiveAction(name="jump", params={})
        new_state = adapter.step(jump_action)
        print("   ✅ Received new state after action. Bot position:", new_state.position)

        print("\n--- Healthcheck PASSED ---")

    except zmq.error.ZMQError as e:
        print(f"\n--- Healthcheck FAILED: ZMQ Error ---")
        print(f"Error: {e}")
        print("Is the bot container running and connected to the same Docker network?")
    except Exception as e:
        print(f"\n--- Healthcheck FAILED ---")
        print(f"An unexpected error occurred: {e}")
    finally:
        if adapter:
            adapter.close()

if __name__ == '__main__':
    main()
