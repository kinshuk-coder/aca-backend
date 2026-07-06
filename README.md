---
title: ACA Backend
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
short_description: FastAPI backend for AI Coding Agent
---

# ACA Backend (AI Coding Agent Sandbox Orchestrator)

This repository contains the backend architecture for the **AI Coding Agent (ACA)**. It uses FastAPI for high-performance streaming connections, LangGraph for computational graph state management, and a secure Docker sandbox execution environment to run agent-generated code safely.

Live API Service: [https://kinshuk7-aca-backend.hf.space](https://kinshuk7-aca-backend.hf.space)  
Frontend Client: [https://aca-frontend-zeta.vercel.app](https://aca-frontend-zeta.vercel.app)

## Core Architecture

* **Stateful Orchestration:** Built on **LangGraph**, utilizing a custom state configuration loop capable of routing decisions, tool calls, and error fallback scenarios.
* **Token Optimization Middleware:** Dynamically manages a 30,000-token sliding context window using `mistral-small-2506` for summary processing to prevent upstream rate limit throttling (`429`).
* **Multi-Model Engine:** Offloads structural agent reasoning to `devstral-2512` while processing context summarization via high-throughput tokens-per-minute (TPM) models.
* **State Checkpointing:** Backed by **MongoDB Atlas** via `langgraph-checkpoint-mongodb` to preserve historical message matrices and channel values across application restarts.

## Tech Stack

* **Language Runtime:** Python 3.11
* **Web Framework:** FastAPI + Uvicorn
* **Agent Graph Framework:** LangGraph (LangChain ecosystem)
* **Package Manager:** `uv` (Fast dependency management and system compilation sync)
* **Database Layer:** MongoDB Atlas

## Environment Variables

The application requires the following environment variables to interface with the database and LLM endpoints. 

| Variable | Description |
| :--- | :--- |
| `MISTRAL_API_KEY` | Production API key for Mistral AI platform access. |
| `MONGO_URI` | MongoDB connection string (with authentication credentials). |

> **Note:** For Hugging Face Spaces production deployment, do not upload a local `.env` file. Add these variables via the **Settings -> Variables and secrets** dashboard.

## Local Development (Docker Compose)

The repository comes configured with a dual-layer local environment configuration.

1. Clone the repository:
   ```bash
   git clone https://github.com/kinshuk-coder/aca-backend.git
   cd aca-backend
   ```

2. Spin up the container using Docker Compose:
   ```bash
   docker compose up --build
   ```

This mounts your local directories to `/app` and initializes the container sandbox mapping port `8000`.

## Hugging Face Spaces Deployment

The deployment pipeline relies on the custom container definitions built natively into the `Dockerfile`:

* **Port Routing:** Hugging Face automatically maps inbound proxy layers to target port `7860`.
* **Privilege Separation:** Automatically drops down to a non-root context execution layer (`user` with UID `1000`) to guarantee hosting safety without breaking execution write pathways inside `/app/ai_workspace`.

To manually deploy changes directly to Hugging Face:
```bash
git remote add huggingface https://huggingface.co/spaces/kinshuk7/aca-backend
git push huggingface main
```