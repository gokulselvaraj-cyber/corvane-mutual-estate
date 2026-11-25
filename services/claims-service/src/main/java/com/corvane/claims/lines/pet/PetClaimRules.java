package com.corvane.claims.lines.pet;

import com.corvane.claims.api.ClaimDtos.FnolRequest;
import com.corvane.claims.domain.Reserve;
import com.corvane.claims.lines.LineRules;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.Map;
import java.util.Set;

/**
 * Pet (PET) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book CRB-PET-6.0; edit the rule book, not this file.
 */
public final class PetClaimRules {
    private PetClaimRules() {}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
            Map.entry("ILLNESS", new BigDecimal("1.47")),
            Map.entry("ACCIDENTAL_INJURY", new BigDecimal("1.52")),
            Map.entry("DENTAL", new BigDecimal("1.02")),
            Map.entry("THIRD_PARTY_LIABILITY", new BigDecimal("0.76")),
            Map.entry("STRAYING_ADVERTISING", new BigDecimal("1.22"))
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of("ILLNESS", "THIRD_PARTY_LIABILITY");

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
            Map.entry("ILLNESS", "witness statements; repair estimate from an approved repairer"),
            Map.entry("ACCIDENTAL_INJURY", "medical report; tenancy agreement"),
            Map.entry("DENTAL", "forensic IT report; invoice for emergency repairs"),
            Map.entry("THIRD_PARTY_LIABILITY", "police crime reference; photos of the damage; witness statements; drainage survey"),
            Map.entry("STRAYING_ADVERTISING", "letter of complaint from the third party; repair estimate from an approved repairer")
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual CRB-PET-6.0). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
            Map.entry("ILLNESS", "Request the documents again after 90 days, then close as withdrawn. Appoint a loss adjuster when the estimate exceeds 5 GBP."),
            Map.entry("ACCIDENTAL_INJURY", "Offer a cash settlement up to 250 GBP if the claimant agrees. Escalate to the claims manager above 14 GBP. Use the approved supplier panel; out-of-panel repairs capped at 750 GBP."),
            Map.entry("DENTAL", "Offer a cash settlement up to 500 GBP if the claimant agrees. Appoint a loss adjuster when the estimate exceeds 90 GBP."),
            Map.entry("THIRD_PARTY_LIABILITY", "Instruct a specialist within 7 hours of notification. Do not pay before the 180-day cooling-off for disputed liability. Ask the fraud team to review if the policy is under 14 days old."),
            Map.entry("STRAYING_ADVERTISING", "Appoint a loss adjuster when the estimate exceeds 15000 GBP. Escalate to the claims manager above 7500 GBP.")
    );

    static final int REPORTING_WINDOW_DAYS = 14;
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("75000");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("0.10");

    @Component
    public static class Validator implements LineRules.LineValidator {
        @Override public String lineCode() { return "PET"; }

        @Override
        public void validate(FnolRequest request) {
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {
                throw new IllegalArgumentException("PET: unknown loss cause " + request.lossCause());
            }
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {
                throw new IllegalArgumentException("PET: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {
                throw new IllegalArgumentException("PET: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }
            if ("DENTAL".equals(request.lossCause()) && request.estimatedAmount().compareTo(new BigDecimal("1500")) > 0) {
                throw new IllegalArgumentException("PET: dental capped at 1,500 per condition");
            }
        }
    }

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {
        @Override public String lineCode() { return "PET"; }

        @Override
        public Reserve initialReserve(FnolRequest request) {
            BigDecimal factor = RESERVE_FACTORS.getOrDefault(request.lossCause(), BigDecimal.ONE);
            BigDecimal indemnity = request.estimatedAmount().multiply(factor).setScale(2, RoundingMode.HALF_UP);
            BigDecimal floor = new BigDecimal("50");
            if (indemnity.compareTo(floor) < 0) {
                indemnity = floor;
            }
            if (ALWAYS_REFER.contains(request.lossCause())) {
                indemnity = indemnity.multiply(new BigDecimal("1.46")).setScale(2, RoundingMode.HALF_UP);
            }
            BigDecimal expenses = indemnity.multiply(EXPENSE_LOADING).setScale(2, RoundingMode.HALF_UP);
            return new Reserve("PET", indemnity, expenses);
        }
    }
}
