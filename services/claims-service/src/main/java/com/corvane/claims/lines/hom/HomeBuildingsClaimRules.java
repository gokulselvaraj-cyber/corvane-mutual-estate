package com.corvane.claims.lines.hom;

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
 * HomeBuildings (HOM) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book CRB-HOM-5.3; edit the rule book, not this file.
 */
public final class HomeBuildingsClaimRules {
    private HomeBuildingsClaimRules() {}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
            Map.entry("ESCAPE_OF_WATER", new BigDecimal("1.09")),
            Map.entry("STORM", new BigDecimal("0.84")),
            Map.entry("SUBSIDENCE", new BigDecimal("1.59")),
            Map.entry("FIRE", new BigDecimal("0.61")),
            Map.entry("FLOOD", new BigDecimal("1.00")),
            Map.entry("IMPACT", new BigDecimal("0.83")),
            Map.entry("MALICIOUS_DAMAGE", new BigDecimal("0.79"))
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of("SUBSIDENCE");

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
            Map.entry("ESCAPE_OF_WATER", "vet invoice; bank statements for the period; witness statements"),
            Map.entry("STORM", "proof of purchase or valuation; photos of the damage; witness statements; forensic IT report"),
            Map.entry("SUBSIDENCE", "weather station report for the date; booking confirmation"),
            Map.entry("FIRE", "letter of complaint from the third party; drainage survey"),
            Map.entry("FLOOD", "repair estimate from an approved repairer; bank statements for the period; drainage survey"),
            Map.entry("IMPACT", "loss adjuster's site report; carrier's bill of lading; witness statements; medical report"),
            Map.entry("MALICIOUS_DAMAGE", "carrier's bill of lading; tenancy agreement; forensic IT report; repair estimate from an approved repairer")
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual CRB-HOM-5.3). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
            Map.entry("ESCAPE_OF_WATER", "Do not pay before the 30-day cooling-off for disputed liability. Request the documents again after 30 days, then close as withdrawn."),
            Map.entry("STORM", "Appoint a loss adjuster when the estimate exceeds 5 GBP. Ask the fraud team to review if the policy is under 60 days old. Arrange an inspection within 90 working days."),
            Map.entry("SUBSIDENCE", "Arrange an inspection within 90 working days. Do not pay before the 3-day cooling-off for disputed liability."),
            Map.entry("FIRE", "Ask the fraud team to review if the policy is under 180 days old. Escalate to the claims manager above 5 GBP."),
            Map.entry("FLOOD", "Arrange an inspection within 15000 working days. Appoint a loss adjuster when the estimate exceeds 7500 GBP. Instruct a specialist within 5 hours of notification."),
            Map.entry("IMPACT", "Appoint a loss adjuster when the estimate exceeds 10 GBP. Ask the fraud team to review if the policy is under 60 days old."),
            Map.entry("MALICIOUS_DAMAGE", "Request the documents again after 60 days, then close as withdrawn. Ask the fraud team to review if the policy is under 5 days old. Escalate to the claims manager above 15000 GBP.")
    );

    static final int REPORTING_WINDOW_DAYS = 31;
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("5000");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("0.12");

    @Component
    public static class Validator implements LineRules.LineValidator {
        @Override public String lineCode() { return "HOM"; }

        @Override
        public void validate(FnolRequest request) {
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {
                throw new IllegalArgumentException("HOM: unknown loss cause " + request.lossCause());
            }
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {
                throw new IllegalArgumentException("HOM: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {
                throw new IllegalArgumentException("HOM: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }
            // no line-specific checks
        }
    }

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {
        @Override public String lineCode() { return "HOM"; }

        @Override
        public Reserve initialReserve(FnolRequest request) {
            BigDecimal factor = RESERVE_FACTORS.getOrDefault(request.lossCause(), BigDecimal.ONE);
            BigDecimal indemnity = request.estimatedAmount().multiply(factor).setScale(2, RoundingMode.HALF_UP);
            BigDecimal floor = new BigDecimal("50");
            if (indemnity.compareTo(floor) < 0) {
                indemnity = floor;
            }
            if (ALWAYS_REFER.contains(request.lossCause())) {
                indemnity = indemnity.multiply(new BigDecimal("1.45")).setScale(2, RoundingMode.HALF_UP);
            }
            BigDecimal expenses = indemnity.multiply(EXPENSE_LOADING).setScale(2, RoundingMode.HALF_UP);
            return new Reserve("HOM", indemnity, expenses);
        }
    }
}
