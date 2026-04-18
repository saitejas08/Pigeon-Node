# 🦅 Project Pigeon: Decentralized Network Surveillance

**Project Pigeon** is an end-to-end distributed Web3 architecture designed to intercept raw mempool transactions, cryptographically encrypt the source IP addresses, and calculate geographic network propagation delay ($\Delta t$), monetized via a trustless Zero-Knowledge Smart Contract.

## 🏗️ Architecture Overview

The system is divided into three distinct microservices:

1. **Stage 1: The Sensor Swarm (`/go-ethereum` & `/pigeon-swarm`)**
   * Modified the Go-Ethereum source code to bypass Proof-of-Stake Beacon client synchronization requirements.
   * Injected asynchronous goroutines into the devP2P networking layer to capture unconfirmed transaction hashes and their broadcasting IP addresses while sitting at Block 0.
   * Deployed as a Dockerized fleet to ensure horizontal scalability and bypass UDP firewall restrictions via host networking.

2. **Stage 2: The Command Center (`/pigeon-command-center`)**
   * A high-frequency Python FastAPI ingestion engine.
   * Implements robust SQLAlchemy connection pooling to handle massive asynchronous transaction dumps without file descriptor exhaustion (`Errno 24`).
   * Encrypts raw IPs with a 32-byte hexadecimal salt into a Keccak-256 commitment, destroying the raw IP from memory.
   * Stores proofs in a PostgreSQL vault with nanosecond-precision timestamps to calculate network triangulation delay ($\Delta t$).

3. **Stage 3: The Trustless Escrow (`/pigeon-contract`)**
   * A Solidity Smart Contract (`PigeonBounty.sol`) deployed via Hardhat.
   * Allows investigators to lock ETH bounties for specific `tx_hash` targets.
   * The Command Center automatically fulfills bounties by submitting the raw IP and salt. The contract hashes the data on-chain, verifies it against the prior cryptographic commitment, and trustlessly releases the funds.

## 🚀 Key Engineering Challenges Solved
* **Memory Leaks & Socket Exhaustion:** Engineered a global throttled HTTP client in Go (`MaxIdleConns: 50`) to prevent the Geth nodes from DDoS-ing the local Python API during massive mempool dumps.
* **Port Collisions:** Architected the Docker Swarm orchestrator with isolated internal Engine API ports (`8551`, `8552`, `8553`) to allow multiple nodes to run on the same host network.
* **Data Sanitization:** Successfully triangulated live mempool data, isolating historical block-sync data (14+ hour delays) from true live-network geographic latency (~42 seconds).

## 🛠️ Tech Stack
* **Blockchain:** Go (Geth modification), Solidity, Hardhat, Web3.py
* **Backend:** Python 3.11, FastAPI, SQLAlchemy, PostgreSQL
* **Infrastructure:** Docker, Docker Compose, Linux (Fedora)

---
*Developed as a B.Tech Engineering Thesis.*
