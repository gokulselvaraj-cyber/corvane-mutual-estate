package com.corvane.claims.lines.mar;

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
 * MarineCargo (MAR) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book CRB-MAR-6.3; edit the rule book, not this file.
 */
public final class MarineCargoClaimRules {
    private MarineCargoClaimRules() {}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
            Map.entry("GENERAL_AVERAGE", new BigDecimal("1.08")),
            Map.entry("JETTISON", new BigDecimal("1.19")),
            Map.entry("CONTAINER_LOSS", new BigDecimal("1.58")),
            Map.entry("WATER_INGRESS", new BigDecimal("1.01")),
            Map.entry("PILFERAGE", new BigDecimal("1.02"))
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of("WATER_INGRESS");

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
            Map.entry("GENERAL_AVERAGE", "loss adjuster's site report; drainage survey"),
            Map.entry("JETTISON", "photos of the damage; vet invoice; letter of complaint from the third party"),
            Map.entry("CONTAINER_LOSS", "vet invoice; repair estimate from an approved repairer; weather station report for the date; loss adjuster's site report"),
            Map.entry("WATER_INGRESS", "weather station report for the date; forensic IT report; witness statements; invoice for emergency repairs"),
            Map.entry("PILFERAGE", "proof of purchase or valuation; drainage survey; police crime reference")
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual CRB-MAR-6.3). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
            Map.entry("GENERAL_AVERAGE", "Ask the fraud team to review if the policy is under 14 days old. Appoint a loss adjuster when the estimate exceeds 1000 GBP."),
            Map.entry("JETTISON", "Appoint a loss adjuster when the estimate exceeds 500 GBP. Request the documents again after 10 days, then close as withdrawn. Do not pay before the 10-day cooling-off for disputed liability."),
            Map.entry("CONTAINER_LOSS", "Appoint a loss adjuster when the estimate exceeds 250 GBP. Ask the fraud team to review if the policy is under 180 days old. Arrange an inspection within 250 working days."),
            Map.entry("WATER_INGRESS", "Arrange an inspection within 5 working days. Use the approved supplier panel; out-of-panel repairs capped at 15000 GBP."),
            Map.entry("PILFERAGE", "Check for a prior claim on the same item within 30 days. Ask the fraud team to review if the policy is under 14 days old. Offer a cash settlement up to 21 GBP if the claimant agrees.")
    );

    static final int REPORTING_WINDOW_DAYS = 14;
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("1000000");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("0.05");

    @Component
    public static class Validator implements LineRules.LineValidator {
        @Override public String lineCode() { return "MAR"; }

        @Override
        public void validate(FnolRequest request) {
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {
                throw new IllegalArgumentException("MAR: unknown loss cause " + request.lossCause());
            }
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {
                throw new IllegalArgumentException("MAR: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {
                throw new IllegalArgumentException("MAR: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }
            // no line-specific checks
        }
    }

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {
        @Override public String lineCode() { return "MAR"; }

        @Override
        public Reserve initialReserve(FnolRequest request) {
            BigDecimal factor = RESERVE_FACTORS.getOrDefault(request.lossCause(), BigDecimal.ONE);
            BigDecimal indemnity = request.estimatedAmount().multiply(factor).setScale(2, RoundingMode.HALF_UP);
            BigDecimal floor = new BigDecimal("250");
            if (indemnity.compareTo(floor) < 0) {
                indemnity = floor;
            }
            if (ALWAYS_REFER.contains(request.lossCause())) {
                indemnity = indemnity.multiply(new BigDecimal("1.36")).setScale(2, RoundingMode.HALF_UP);
            }
            BigDecimal expenses = indemnity.multiply(EXPENSE_LOADING).setScale(2, RoundingMode.HALF_UP);
            return new Reserve("MAR", indemnity, expenses);
        }
    }
}
