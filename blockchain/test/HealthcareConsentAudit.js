const {expect}=require("chai");
const {ethers}=require("hardhat");
describe("HealthcareConsentAudit",()=>{
  it("enforces provider and revocation checks",async()=>{
    const [owner,a,b]=await ethers.getSigners();
    const F=await ethers.getContractFactory("HealthcareConsentAudit");
    const c=await F.deploy(); await c.waitForDeployment();
    const model=ethers.id("MODEL_V1"), purpose=ethers.id("NON_CLINICAL_SCORING");
    const consent=ethers.id("CONSENT_1");
    await c.registerModel(model);
    await c.grantConsent(consent,ethers.id("SUBJECT_1"),a.address,model,purpose,
      Math.floor(Date.now()/1000)+3600);
    expect(await c.canInfer(consent,a.address,model,purpose)).to.equal(true);
    expect(await c.canInfer(consent,b.address,model,purpose)).to.equal(false);
    await c.revokeConsent(consent);
    expect(await c.canInfer(consent,a.address,model,purpose)).to.equal(false);
  });
});
