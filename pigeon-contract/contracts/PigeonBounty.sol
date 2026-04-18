// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract PigeonBounty {
    // The wallet address of your Python Command Center
    address public oracleNode; 

    struct Bounty {
        address investigator;
        uint256 amount;
        bool isFulfilled;
        string revealedIP;
    }

    // Mapping from an Ethereum tx_hash to a Bounty
    mapping(string => Bounty) public bounties;

    // Events allow your Python API to "listen" to the blockchain
    event BountyPlaced(string txHash, address investigator, uint256 amount);
    event BountyFulfilled(string txHash, string ipAddress);

    constructor() {
        // Whoever deploys this contract is the trusted Pigeon Oracle
        oracleNode = msg.sender; 
    }

    // --- 1. THE REQUEST (Investigator places the bounty) ---
    function placeBounty(string memory txHash) external payable {
        require(msg.value > 0, "Bounty must be greater than 0 ETH");
        require(bounties[txHash].investigator == address(0), "Bounty already exists for this transaction");

        bounties[txHash] = Bounty({
            investigator: msg.sender,
            amount: msg.value,
            isFulfilled: false,
            revealedIP: ""
        });

        emit BountyPlaced(txHash, msg.sender, msg.value);
    }

    // --- 2. THE DELIVERY & VERIFICATION (Python API fulfills it) ---
    function fulfillBounty(
        string memory txHash, 
        string memory ipAddress, 
        string memory salt, 
        bytes32 priorCommitment
    ) external {
        require(msg.sender == oracleNode, "Security: Only the Pigeon Swarm can fulfill bounties");
        
        Bounty storage b = bounties[txHash];
        require(b.amount > 0, "No bounty exists for this transaction");
        require(!b.isFulfilled, "Bounty has already been fulfilled");

        // THE CRYPTOGRAPHIC PROOF:
        // The contract hashes the raw IP and Salt exactly like the Python API did.
        // It must perfectly match the commitment.
        bytes32 calculatedHash = keccak256(abi.encodePacked(ipAddress, salt));
        require(calculatedHash == priorCommitment, "Zero-Knowledge Failure: Hash does not match commitment");

        // If the math proves out, update the state
        b.revealedIP = ipAddress;
        b.isFulfilled = true;

        // Release the ETH bounty to the Command Center wallet
        payable(oracleNode).transfer(b.amount);

        // Broadcast the IP to the investigator
        emit BountyFulfilled(txHash, ipAddress);
    }
}
