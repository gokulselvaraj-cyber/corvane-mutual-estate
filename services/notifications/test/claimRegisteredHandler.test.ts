import { ClaimRegisteredHandler } from "../src/handlers/claimRegisteredHandler";

test("emails and texts the claimant with the line-specific template", async () => {
  const mailer = { send: jest.fn().mockResolvedValue(undefined) } as any;
  const sms = { send: jest.fn().mockResolvedValue(undefined) } as any;
  await new ClaimRegisteredHandler(mailer, sms).handle({
    claimId: "CLM-1", policyNumber: "PET-9", lineCode: "PET", claimantName: "A Tester",
    claimantEmail: "a@example.test", claimantMobile: "+447700900000", triageOutcome: "ADJUSTER",
  });
  expect(mailer.send).toHaveBeenCalledWith("a@example.test", "Your claim CLM-1 is registered",
    "claim-registered-pet", expect.objectContaining({ line: "Pet", autoApproved: false }));
  expect(sms.send).toHaveBeenCalledTimes(1);
});
