const hre=require("hardhat");
async function main(){
  const F=await hre.ethers.getContractFactory("HealthcareConsentAudit");
  const c=await F.deploy(); await c.waitForDeployment();
  console.log("HealthcareConsentAudit:",await c.getAddress());
}
main().catch(e=>{console.error(e);process.exitCode=1;});
