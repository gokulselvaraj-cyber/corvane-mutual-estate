import { STEPS } from "./FnolWizard";

describe("FnolWizard", () => {
  it("has the five FNOL steps in order", () =>
    expect(STEPS).toEqual(["PolicyLookup", "IncidentDetails", "DamageAndPhotos", "Review", "Submit"]));
});
