# Project Pigeon: Decentralized Network Surveillance

**Project Pigeon** is an end-to-end distributed Web3 architecture designed to intercept raw mempool transactions, cryptographically encrypt the source IP addresses, and calculate geographic network propagation delay ($\Delta t$), monetized via a trustless Zero-Knowledge Smart Contract.

## Architecture Overview

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

## Key Engineering Challenges Solved
* **Memory Leaks & Socket Exhaustion:** Engineered a global throttled HTTP client in Go (`MaxIdleConns: 50`) to prevent the Geth nodes from DDoS-ing the local Python API during massive mempool dumps.
* **Port Collisions:** Architected the Docker Swarm orchestrator with isolated internal Engine API ports (`8551`, `8552`, `8553`) to allow multiple nodes to run on the same host network.
* **Data Sanitization:** Successfully triangulated live mempool data, isolating historical block-sync data (14+ hour delays) from true live-network geographic latency (~42 seconds).

## Tech Stack
* **Blockchain:** Go (Geth modification), Solidity, Hardhat, Web3.py
* **Backend:** Python 3.11, FastAPI, SQLAlchemy, PostgreSQL
* **Infrastructure:** Docker, Docker Compose, Linux (Fedora)

---

## How to Run the Simulation

This section details the Official Launch Sequence to boot the architecture from a cold start and verify the end-to-end data flow.

### Prerequisites
* Docker & Docker Compose
* Node.js & npm (for Hardhat)
* Python 3.11+ & `web3.py`

### Phase 1: Establish the Local Blockchain
Open **Terminal 1** and spin up the local Hardhat testing network. Leave this tab running.
```bash
cd pigeon-contract
npx hardhat node
```

### Phase 2: Boot the Command Center
Open **Terminal 2**. Bring the PostgreSQL database and FastAPI ingestion engine online *before* launching the swarm.
```bash
cd pigeon-command-center
docker-compose up -d
```
**Verification:** Purge any residual database history to ensure a clean experiment.
```bash
docker exec -it postgres-vault psql -U postgres -d pigeondb -c "TRUNCATE TABLE intercepts RESTART IDENTITY;"
```

### Phase 3: Unleash the Sensor Swarm
Still in **Terminal 2**, deploy the modified Ethereum nodes.
```bash
cd ../pigeon-swarm
docker-compose up -d
```
**Verification:** Wait ~3 minutes for the nodes to auto-discover peers. Ensure the database is successfully capturing encrypted network traffic:
```bash
docker exec -it postgres-vault psql -U postgres -d pigeondb -c "SELECT count(*) FROM intercepts;"
```

### Phase 4: Calculate Geographic Delay (Delta-T)
Once data is flowing, query the vault to prove that multiple distributed nodes captured the exact same transaction, and calculate the network latency. Copy one of the resulting `tx_hash` values for the next step.
```bash
docker exec -it postgres-vault psql -U postgres -d pigeondb -c "SELECT tx_hash, COUNT(DISTINCT node_id) as nodes_caught, MIN(timestamp) as first_seen, MAX(timestamp) as last_seen, (MAX(timestamp) - MIN(timestamp)) AS delta_t_seconds FROM intercepts GROUP BY tx_hash HAVING COUNT(DISTINCT node_id) > 1 ORDER BY delta_t_seconds ASC LIMIT 5;"
```

### Phase 5: The Trustless Escrow (Monetization)
Open **Terminal 3**. Deploy the smart contract to your local blockchain.
```bash
cd pigeon-contract
npx hardhat ignition deploy ignition/modules/PigeonBounty.ts --network localhost
```
Execute the Python bridge script using a captured transaction hash. This simulates an investigator placing a bounty, and the Command Center trustlessly fulfilling it via cryptographic proof.
```bash
# Usage: python3 thesis_demo.py <TX_HASH> <OPTIONAL_IP>
python3 thesis_demo.py 0xYOUR_CAPTURED_TX_HASH 152.58.180.156
```
**Verification:** The terminal will output `🎉 TRUSTLESS ESCROW COMPLETE!` confirming the on-chain math verified the off-chain Postgres data.

### Graceful Shutdown
To tear down the architecture and free up system resources:
```bash
cd pigeon-swarm && docker-compose down
cd ../pigeon-command-center && docker-compose down
```

---
*Developed as a B.Tech Engineering Project*
