import { Mailer } from "../channels/mailer";
import { lineName } from "../lines";

export interface PolicyBound { policyNumber: string; lineCode: string; holderName: string; holderEmail: string;
  annualPremium: string; currency: string; inceptionDate: string }

export class PolicyBoundHandler {
  constructor(private mailer: Mailer) {}

  async handle(evt: PolicyBound): Promise<void> {
    await this.mailer.send(evt.holderEmail, `Welcome to Corvane: policy ${evt.policyNumber}`, "policy-welcome", {
      name: evt.holderName, policyNumber: evt.policyNumber, line: lineName(evt.lineCode),
      premium: `${evt.annualPremium} ${evt.currency}`, start: evt.inceptionDate,
    });
  }
}
