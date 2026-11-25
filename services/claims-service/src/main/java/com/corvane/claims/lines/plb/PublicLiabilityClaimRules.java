package com.corvane.claims.lines.plb;

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
 * PublicLiability (PLB) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book CRB-PLB-9.3; edit the rule book, not this file.
 */
public final class PublicLiabilityClaimRules {
    private PublicLiabilityClaimRules() {}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
            Map.entry("SLIP_TRIP_FALL", new BigDecimal("0.87")),
            Map.entry("PROPERTY_DAMAGE_THIRD_PARTY", new BigDecimal("1.15")),
            Map.entry("PRODUCT_INJURY", new BigDecimal("1.12")),
            Map.entry("FOOD_POISONING", new BigDecimal("0.61"))
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of("PRODUCT_INJURY", "SLIP_TRIP_FALL");

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
            Map.entry("SLIP_TRIP_FALL", "letter of complaint from the third party; photos of the damage; drainage survey; forensic IT report"),
            Map.entry("PROPERTY_DAMAGE_THIRD_PARTY", "proof of purchase or valuation; vet invoice"),
            Map.entry("PRODUCT_INJURY", "invoice for emergency repairs; vet invoice; loss adjuster's site report"),
            Map.entry("FOOD_POISONING", "forensic IT report; repair estimate from an approved repairer; carrier's bill of lading; weather station report for the date")
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual CRB-PLB-9.3). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
            Map.entry("SLIP_TRIP_FALL", "Check for a prior claim on the same item within 14 days. Use the approved supplier panel; out-of-panel repairs capped at 250 GBP."),
            Map.entry("PROPERTY_DAMAGE_THIRD_PARTY", "Escalate to the claims manager above 3 GBP. Arrange an inspection within 500 working days. Request the documents again after 14 days, then close as withdrawn."),
            Map.entry("PRODUCT_INJURY", "Escalate to the claims manager above 14 GBP. Appoint a loss adjuster when the estimate exceeds 2500 GBP."),
            Map.entry("FOOD_POISONING", "Appoint a loss adjuster when the estimate exceeds 7500 GBP. Offer a cash settlement up to 1000 GBP if the claimant agrees.")
    );

    static final int REPORTING_WINDOW_DAYS = 31;
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("2500");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("0.17");

    @Component
    public static class Validator implements LineRules.LineValidator {
        @Override public String lineCode() { return "PLB"; }

        @Override
        public void validate(FnolRequest request) {
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {
                throw new IllegalArgumentException("PLB: unknown loss cause " + request.lossCause());
            }
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {
                throw new IllegalArgumentException("PLB: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {
                throw new IllegalArgumentException("PLB: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }
            // no line-specific checks
        }
    }

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {
        @Override public String lineCode() { return "PLB"; }

        @Override
        public Reserve initialReserve(FnolRequest request) {
            BigDecimal factor = RESERVE_FACTORS.getOrDefault(request.lossCause(), BigDecimal.ONE);
            BigDecimal indemnity = request.estimatedAmount().multiply(factor).setScale(2, RoundingMode.HALF_UP);
            BigDecimal floor = new BigDecimal("100");
            if (indemnity.compareTo(floor) < 0) {
                indemnity = floor;
            }
            if (ALWAYS_REFER.contains(request.lossCause())) {
                indemnity = indemnity.multiply(new BigDecimal("1.14")).setScale(2, RoundingMode.HALF_UP);
            }
            BigDecimal expenses = indemnity.multiply(EXPENSE_LOADING).setScale(2, RoundingMode.HALF_UP);
            return new Reserve("PLB", indemnity, expenses);
        }
    }
}
