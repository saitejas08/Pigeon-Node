import sys
import json
import secrets
from web3 import Web3

# --- 0. CLI Argument Handling ---
if len(sys.argv) < 2:
    print("❌ Error: Missing Transaction Hash.")
    print("Usage: python3 thesis_demo.py <TX_HASH> [RAW_IP]")
    sys.exit(1)

target_tx = sys.argv[1]
# If you don't provide an IP, it defaults to the mock one
target_ip = sys.argv[2] if len(sys.argv) > 2 else "152.58.180.156"

# --- 1. Connect to the local Hardhat Blockchain ---
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
print(f"🔗 Connected to Blockchain: {w3.is_connected()}")

# --- 2. Load the Smart Contract ---
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
with open("artifacts/contracts/PigeonBounty.sol/PigeonBounty.json") as f:
    artifact = json.load(f)
    
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=artifact["abi"])

# --- 3. Define the Actors (From Hardhat Node) ---
oracle_address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
oracle_pkey = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

investigator_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
investigator_pkey = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

# --- 4. Generate the Cryptographic Proof ---
salt = secrets.token_hex(32) 
commitment = w3.keccak(text=target_ip + salt) 

print("\n==================================================")
print("🕵️‍♂️ STAGE A: INVESTIGATOR PLACES 1 ETH BOUNTY")
print("==================================================")
# The Investigator locks 1 ETH into the Smart Contract asking for the IP behind target_tx
tx = contract.functions.placeBounty(target_tx).build_transaction({
    'from': investigator_address,
    'value': w3.to_wei(1, 'ether'),
    'nonce': w3.eth.get_transaction_count(investigator_address)
})
signed_tx = w3.eth.account.sign_transaction(tx, investigator_pkey)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
w3.eth.wait_for_transaction_receipt(tx_hash)

bounty_data = contract.functions.bounties(target_tx).call()
print(f"✅ Bounty Placed by: {bounty_data[0]}")
print(f"✅ Amount Locked: {w3.from_wei(bounty_data[1], 'ether')} ETH")

print("\n==================================================")
print("🦅 STAGE B: COMMAND CENTER FULFILLS BOUNTY")
print("==================================================")
# The Oracle sees the bounty, pulls the IP and Salt from the DB, and submits it
print(f"Submitting Raw IP: {target_ip}")
print(f"Submitting Salt: {salt}")

tx2 = contract.functions.fulfillBounty(
    target_tx, 
    target_ip, 
    salt, 
    commitment
).build_transaction({
    'from': oracle_address,
    'nonce': w3.eth.get_transaction_count(oracle_address)
})
signed_tx2 = w3.eth.account.sign_transaction(tx2, oracle_pkey)
tx_hash2 = w3.eth.send_raw_transaction(signed_tx2.raw_transaction)
w3.eth.wait_for_transaction_receipt(tx_hash2)

# Verify the result on the blockchain
final_bounty = contract.functions.bounties(target_tx).call()
print("\n🎉 TRUSTLESS ESCROW COMPLETE!")
print(f"On-Chain Revealed IP: {final_bounty[3]}")
print(f"Bounty Claimed: {final_bounty[2]}")
