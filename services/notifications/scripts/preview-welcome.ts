// Renders the policy-welcome template for the content team to review, without sending anything.
// Run with: npx ts-node scripts/preview-welcome.ts > welcome.html
// The policyholder below is made up (example.com is reserved for examples); never paste a real customer here.
import { Mailer } from "../src/channels/mailer";
import { lineName } from "../src/lines";

const samplePolicyholder = {
  policyNumber: "HOM-00045678", lineCode: "HOM", holderName: "Pat Hughes", holderEmail: "pat.hughes@example.com",
  annualPremium: "318.00", currency: "GBP", inceptionDate: "2026-12-01",
};

const mailer = new Mailer({ host: "localhost", port: 1025, user: "", password: "", from: "preview@corvane.example" });
process.stdout.write(mailer.render("policy-welcome", {
  name: samplePolicyholder.holderName, policyNumber: samplePolicyholder.policyNumber,
  line: lineName(samplePolicyholder.lineCode),
  premium: `${samplePolicyholder.annualPremium} ${samplePolicyholder.currency}`, start: samplePolicyholder.inceptionDate,
}));
