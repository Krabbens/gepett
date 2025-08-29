# Gepett: A Game-Agnostic Agent System for Minecraft

This repository contains the complete source code for **Gepett**, an agent system designed for Minecraft running on a headless Linux server with CUDA support. The system is architected to be game-agnostic, with a specific adapter for Minecraft.

## Project Goals

- **Headless Operation**: Designed for Linux servers (Ubuntu 20.04+, Debian 12+) without a graphical interface, accessible via SSH only.
- **CUDA Acceleration**: Leverages NVIDIA GPUs for all heavy computation, including LLM inference, world model training, and reinforcement learning.
- **Modularity**: Composed of distinct, interchangeable modules for perception, planning, learning, and execution.
- **Reproducibility**: All components are managed via Docker and Docker Compose to ensure a consistent and reproducible environment.

## Architecture Overview

The system consists of three main parts:
1.  **Minecraft Server**: A PaperMC server running the game world.
2.  **Bot Client (Node.js)**: A Mineflayer-based bot that connects to the server and acts as the low-level interface to the game.
3.  **Core Agent (Python)**: The "brain" of the agent, handling perception, planning (LLM), learning (RL, World Model), and memory (HBM).

Communication between the Bot and the Core Agent is handled by ZeroMQ.

## Getting Started

### Prerequisites
- Docker
- NVIDIA Container Toolkit
- Git

### Installation & Launch

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd gepett-cuda-headless
    ```

2.  **Set up CUDA environment (if running bare-metal):**
    ```bash
    ./scripts/setup_cuda.sh
    ```

3.  **Build and run all services using Docker Compose:**
    ```bash
    docker compose up --build
    ```
    This command will:
    - Build the Docker image for the core agent.
    - Download and set up the PaperMC server.
    - Install dependencies for the Node.js bot.
    - Launch the server, bot, and core agent services.

### Running Pipelines

- **Symbolic-only pipeline:**
  ```bash
  ./scripts/run_pipeline_symbolic.sh
  ```

- **Full pipeline (with vision):**
  ```bash
  ./scripts/run_pipeline_full.sh
  ```

## Repository Structure

(A brief overview of the directory structure will be added here.)
