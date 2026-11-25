import { Mailer } from "../channels/mailer";
import { SmsClient } from "../channels/smsClient";
import { config } from "../config";
import { lineName } from "../lines";

export interface ClaimRegistered {
  claimId: string; policyNumber: string; lineCode: string; claimantName: string;
  claimantEmail?: string; claimantMobile?: string; triageOutcome: "AUTO_APPROVED" | "ADJUSTER";
}

/** Last hop of journey J1 (FNOL): tells the customer their claim is registered. */
export class ClaimRegisteredHandler {
  constructor(private mailer: Mailer, private sms: SmsClient) {}

  async handle(evt: ClaimRegistered): Promise<void> {
    const data = {
      name: evt.claimantName, claimId: evt.claimId, line: lineName(evt.lineCode),
      autoApproved: evt.triageOutcome === "AUTO_APPROVED",
      trackUrl: `${config.portalUrl}/claims/${evt.claimId}`,
    };
    const template = `claim-registered-${evt.lineCode.toLowerCase()}`;
    if (evt.claimantEmail) {
      await this.mailer.send(evt.claimantEmail, `Your claim ${evt.claimId} is registered`, template, data);
    }
    if (evt.claimantMobile) {
      await this.sms.send(evt.claimantMobile, `Corvane: claim ${evt.claimId} registered. Track it at ${data.trackUrl}`);
    }
  }
}
