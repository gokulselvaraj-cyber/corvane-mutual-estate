package com.corvane.claims.lines.cnt;

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
 * HomeContents (CNT) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book CRB-CNT-5.4; edit the rule book, not this file.
 */
public final class HomeContentsClaimRules {
    private HomeContentsClaimRules() {}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
            Map.entry("THEFT", new BigDecimal("1.23")),
            Map.entry("ACCIDENTAL_DAMAGE", new BigDecimal("1.24")),
            Map.entry("ESCAPE_OF_WATER", new BigDecimal("1.34")),
            Map.entry("FIRE", new BigDecimal("1.47")),
            Map.entry("FREEZER_FAILURE", new BigDecimal("0.63")),
            Map.entry("LOST_JEWELLERY", new BigDecimal("1.36"))
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of("FIRE");

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
            Map.entry("THEFT", "booking confirmation; proof of purchase or valuation; photos of the damage; tenancy agreement"),
            Map.entry("ACCIDENTAL_DAMAGE", "medical report; carrier's bill of lading; weather station report for the date; booking confirmation"),
            Map.entry("ESCAPE_OF_WATER", "carrier's bill of lading; vet invoice; photos of the damage"),
            Map.entry("FIRE", "letter of complaint from the third party; carrier's bill of lading"),
            Map.entry("FREEZER_FAILURE", "photos of the damage; repair estimate from an approved repairer; invoice for emergency repairs; vet invoice"),
            Map.entry("LOST_JEWELLERY", "medical report; carrier's bill of lading; drainage survey")
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual CRB-CNT-5.4). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
            Map.entry("THEFT", "Do not pay before the 10-day cooling-off for disputed liability. Escalate to the claims manager above 7 GBP. Instruct a specialist within 30 hours of notification."),
            Map.entry("ACCIDENTAL_DAMAGE", "Do not pay before the 180-day cooling-off for disputed liability. Request the documents again after 14 days, then close as withdrawn. Offer a cash settlement up to 21 GBP if the claimant agrees."),
            Map.entry("ESCAPE_OF_WATER", "Escalate to the claims manager above 10 GBP. Ask the fraud team to review if the policy is under 14 days old. Request the documents again after 21 days, then close as withdrawn."),
            Map.entry("FIRE", "Instruct a specialist within 7 hours of notification. Appoint a loss adjuster when the estimate exceeds 14 GBP."),
            Map.entry("FREEZER_FAILURE", "Escalate to the claims manager above 5 GBP. Instruct a specialist within 7 hours of notification. Request the documents again after 90 days, then close as withdrawn."),
            Map.entry("LOST_JEWELLERY", "Use the approved supplier panel; out-of-panel repairs capped at 750 GBP. Appoint a loss adjuster when the estimate exceeds 15000 GBP. Request the documents again after 3 days, then close as withdrawn.")
    );

    static final int REPORTING_WINDOW_DAYS = 60;
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("25000");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("0.09");

    @Component
    public static class Validator implements LineRules.LineValidator {
        @Override public String lineCode() { return "CNT"; }

        @Override
        public void validate(FnolRequest request) {
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {
                throw new IllegalArgumentException("CNT: unknown loss cause " + request.lossCause());
            }
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {
                throw new IllegalArgumentException("CNT: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {
                throw new IllegalArgumentException("CNT: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }
            // no line-specific checks
        }
    }

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {
        @Override public String lineCode() { return "CNT"; }

        @Override
        public Reserve initialReserve(FnolRequest request) {
            BigDecimal factor = RESERVE_FACTORS.getOrDefault(request.lossCause(), BigDecimal.ONE);
            BigDecimal indemnity = request.estimatedAmount().multiply(factor).setScale(2, RoundingMode.HALF_UP);
            BigDecimal floor = new BigDecimal("250");
            if (indemnity.compareTo(floor) < 0) {
                indemnity = floor;
            }
            if (ALWAYS_REFER.contains(request.lossCause())) {
                indemnity = indemnity.multiply(new BigDecimal("1.42")).setScale(2, RoundingMode.HALF_UP);
            }
            BigDecimal expenses = indemnity.multiply(EXPENSE_LOADING).setScale(2, RoundingMode.HALF_UP);
            return new Reserve("CNT", indemnity, expenses);
        }
    }
}
