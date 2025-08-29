import zmq from 'zeromq';
import config from './config.json' assert { type: 'json' };

class ZMQBridge {
  constructor() {
    this.statePubSocket = new zmq.Publisher();
    this.actionRepSocket = new zmq.Reply();
    this.controlRepSocket = new zmq.Reply();
    console.log('ZMQ sockets created.');
  }

  async start() {
    const { state_pub_endpoint, action_rep_endpoint, control_rep_endpoint } = config.zmq;

    await this.statePubSocket.bind(state_pub_endpoint);
    console.log(`State PUB socket bound to ${state_pub_endpoint}`);

    await this.actionRepSocket.bind(action_rep_endpoint);
    console.log(`Action REP socket bound to ${action_rep_endpoint}`);

    await this.controlRepSocket.bind(control_rep_endpoint);
    console.log(`Control REP socket bound to ${control_rep_endpoint}`);
  }

  /**
   * Publishes a state frame object to the Python core.
   * @param {object} stateFrame The state data to publish.
   */
  async publishState(stateFrame) {
    const message = JSON.stringify(stateFrame);
    await this.statePubSocket.send(['state', message]);
  }

  /**
   * Listens for and handles action requests from the Python core.
   * @param {Function} handler A function that takes the action command and returns a result.
   *                           Example: (cmd) => ({ ok: true, obs: new_state })
   */
  async listenForActions(handler) {
    console.log('Listening for action requests...');
    for await (const [msg] of this.actionRepSocket) {
      try {
        const request = JSON.parse(msg.toString());
        // console.log('Received action request:', request);
        const result = await handler(request);
        await this.actionRepSocket.send(JSON.stringify(result));
      } catch (e) {
        console.error('Error processing action request:', e);
        const errorResponse = { ok: false, error: e.message };
        await this.actionRepSocket.send(JSON.stringify(errorResponse));
      }
    }
  }

  /**
   * Listens for and handles control requests from the Python core.
   * @param {Function} handler A function that takes the control command and returns a result.
   *                           Example: (cmd) => ({ ok: true, message: 'World reset' })
   */
  async listenForControl(handler) {
    console.log('Listening for control requests...');
    for await (const [msg] of this.controlRepSocket) {
      try {
        const request = JSON.parse(msg.toString());
        console.log('Received control request:', request);
        const result = await handler(request);
        await this.controlRepSocket.send(JSON.stringify(result));
      } catch (e) {
        console.error('Error processing control request:', e);
        const errorResponse = { ok: false, error: e.message };
        await this.controlRepSocket.send(JSON.stringify(errorResponse));
      }
    }
  }
}

export const zmqBridge = new ZMQBridge();
