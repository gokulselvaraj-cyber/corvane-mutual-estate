package com.corvane.claims.lines.gdg;

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
 * Gadget (GDG) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book CRB-GDG-6.0; edit the rule book, not this file.
 */
public final class GadgetClaimRules {
    private GadgetClaimRules() {}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
            Map.entry("ACCIDENTAL_DAMAGE", new BigDecimal("1.04")),
            Map.entry("THEFT", new BigDecimal("1.54")),
            Map.entry("LIQUID_DAMAGE", new BigDecimal("0.69")),
            Map.entry("MECHANICAL_BREAKDOWN", new BigDecimal("0.74")),
            Map.entry("LOSS", new BigDecimal("1.12"))
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of("LIQUID_DAMAGE");

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
            Map.entry("ACCIDENTAL_DAMAGE", "vet invoice; invoice for emergency repairs; photos of the damage"),
            Map.entry("THEFT", "tenancy agreement; drainage survey; carrier's bill of lading"),
            Map.entry("LIQUID_DAMAGE", "loss adjuster's site report; drainage survey; booking confirmation; weather station report for the date"),
            Map.entry("MECHANICAL_BREAKDOWN", "invoice for emergency repairs; photos of the damage"),
            Map.entry("LOSS", "drainage survey; proof of purchase or valuation")
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual CRB-GDG-6.0). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
            Map.entry("ACCIDENTAL_DAMAGE", "Use the approved supplier panel; out-of-panel repairs capped at 15000 GBP. Ask the fraud team to review if the policy is under 14 days old."),
            Map.entry("THEFT", "Request the documents again after 5 days, then close as withdrawn. Check for a prior claim on the same item within 10 days. Use the approved supplier panel; out-of-panel repairs capped at 22500 GBP."),
            Map.entry("LIQUID_DAMAGE", "Ask the fraud team to review if the policy is under 3 days old. Appoint a loss adjuster when the estimate exceeds 2500 GBP."),
            Map.entry("MECHANICAL_BREAKDOWN", "Appoint a loss adjuster when the estimate exceeds 7 GBP. Do not pay before the 60-day cooling-off for disputed liability."),
            Map.entry("LOSS", "Offer a cash settlement up to 14 GBP if the claimant agrees. Instruct a specialist within 60 hours of notification. Arrange an inspection within 21 working days.")
    );

    static final int REPORTING_WINDOW_DAYS = 14;
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("25000");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("0.10");

    @Component
    public static class Validator implements LineRules.LineValidator {
        @Override public String lineCode() { return "GDG"; }

        @Override
        public void validate(FnolRequest request) {
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {
                throw new IllegalArgumentException("GDG: unknown loss cause " + request.lossCause());
            }
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {
                throw new IllegalArgumentException("GDG: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {
                throw new IllegalArgumentException("GDG: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }
            if ("LOSS".equals(request.lossCause())) {
                throw new IllegalArgumentException("GDG: loss is covered only on Gadget Plus; route to manual check");
            }
        }
    }

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {
        @Override public String lineCode() { return "GDG"; }

        @Override
        public Reserve initialReserve(FnolRequest request) {
            BigDecimal factor = RESERVE_FACTORS.getOrDefault(request.lossCause(), BigDecimal.ONE);
            BigDecimal indemnity = request.estimatedAmount().multiply(factor).setScale(2, RoundingMode.HALF_UP);
            BigDecimal floor = new BigDecimal("500");
            if (indemnity.compareTo(floor) < 0) {
                indemnity = floor;
            }
            if (ALWAYS_REFER.contains(request.lossCause())) {
                indemnity = indemnity.multiply(new BigDecimal("1.32")).setScale(2, RoundingMode.HALF_UP);
            }
            BigDecimal expenses = indemnity.multiply(EXPENSE_LOADING).setScale(2, RoundingMode.HALF_UP);
            return new Reserve("GDG", indemnity, expenses);
        }
    }
}
