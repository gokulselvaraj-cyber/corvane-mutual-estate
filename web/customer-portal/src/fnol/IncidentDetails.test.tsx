import { validateIncident } from "./steps/IncidentDetails";

const base = { lossDate: "2026-11-01", lossCause: "THEFT", description: "Bike stolen from the locked garage overnight",
  injuryInvolved: false, estimatedAmount: 900, thirdPartyInvolved: false };
const today = new Date("2026-11-16");

describe("validateIncident", () => {
  it("accepts a normal claim", () => expect(validateIncident(base, today)).toEqual([]));
  it("rejects a future loss date", () =>
    expect(validateIncident({ ...base, lossDate: "2026-12-01" }, today)).toContain("The loss date cannot be in the future."));
  it("asks for injury details", () =>
    expect(validateIncident({ ...base, injuryInvolved: true }, today)).toContain("Please tell us about the injury."));
  it("sends old losses to the phone line", () =>
    expect(validateIncident({ ...base, lossDate: "2026-01-01" }, today)).toHaveLength(1));
});
