import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

const PigeonBountyModule = buildModule("PigeonBountyModule", (m) => {
  // This tells Hardhat to grab the compiled PigeonBounty contract and deploy it
  const pigeonBounty = m.contract("PigeonBounty");

  return { pigeonBounty };
});

export default PigeonBountyModule;
