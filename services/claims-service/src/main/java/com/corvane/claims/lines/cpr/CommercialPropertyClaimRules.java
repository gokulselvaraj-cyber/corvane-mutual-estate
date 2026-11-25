package com.corvane.claims.lines.cpr;

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
 * CommercialProperty (CPR) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book CRB-CPR-3.1; edit the rule book, not this file.
 */
public final class CommercialPropertyClaimRules {
    private CommercialPropertyClaimRules() {}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
            Map.entry("FIRE", new BigDecimal("0.92")),
            Map.entry("BUSINESS_INTERRUPTION", new BigDecimal("1.08")),
            Map.entry("MACHINERY_BREAKDOWN", new BigDecimal("1.37")),
            Map.entry("THEFT", new BigDecimal("1.29")),
            Map.entry("FLOOD", new BigDecimal("0.85"))
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of("MACHINERY_BREAKDOWN");

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
            Map.entry("FIRE", "repair estimate from an approved repairer; medical report; photos of the damage"),
            Map.entry("BUSINESS_INTERRUPTION", "drainage survey; proof of purchase or valuation"),
            Map.entry("MACHINERY_BREAKDOWN", "medical report; bank statements for the period"),
            Map.entry("THEFT", "police crime reference; forensic IT report; carrier's bill of lading"),
            Map.entry("FLOOD", "invoice for emergency repairs; vet invoice; police crime reference")
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual CRB-CPR-3.1). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
            Map.entry("FIRE", "Do not pay before the 180-day cooling-off for disputed liability. Request the documents again after 60 days, then close as withdrawn."),
            Map.entry("BUSINESS_INTERRUPTION", "Arrange an inspection within 500 working days. Request the documents again after 60 days, then close as withdrawn."),
            Map.entry("MACHINERY_BREAKDOWN", "Appoint a loss adjuster when the estimate exceeds 2500 GBP. Ask the fraud team to review if the policy is under 60 days old. Use the approved supplier panel; out-of-panel repairs capped at 250 GBP."),
            Map.entry("THEFT", "Request the documents again after 10 days, then close as withdrawn. Arrange an inspection within 90 working days."),
            Map.entry("FLOOD", "Ask the fraud team to review if the policy is under 90 days old. Arrange an inspection within 10 working days.")
    );

    static final int REPORTING_WINDOW_DAYS = 90;
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("1000000");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("0.03");

    @Component
    public static class Validator implements LineRules.LineValidator {
        @Override public String lineCode() { return "CPR"; }

        @Override
        public void validate(FnolRequest request) {
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {
                throw new IllegalArgumentException("CPR: unknown loss cause " + request.lossCause());
            }
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {
                throw new IllegalArgumentException("CPR: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {
                throw new IllegalArgumentException("CPR: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }
            // no line-specific checks
        }
    }

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {
        @Override public String lineCode() { return "CPR"; }

        @Override
        public Reserve initialReserve(FnolRequest request) {
            BigDecimal factor = RESERVE_FACTORS.getOrDefault(request.lossCause(), BigDecimal.ONE);
            BigDecimal indemnity = request.estimatedAmount().multiply(factor).setScale(2, RoundingMode.HALF_UP);
            BigDecimal floor = new BigDecimal("100");
            if (indemnity.compareTo(floor) < 0) {
                indemnity = floor;
            }
            if (ALWAYS_REFER.contains(request.lossCause())) {
                indemnity = indemnity.multiply(new BigDecimal("1.49")).setScale(2, RoundingMode.HALF_UP);
            }
            BigDecimal expenses = indemnity.multiply(EXPENSE_LOADING).setScale(2, RoundingMode.HALF_UP);
            return new Reserve("CPR", indemnity, expenses);
        }
    }
}
