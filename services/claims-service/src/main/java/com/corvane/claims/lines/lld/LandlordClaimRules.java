package com.corvane.claims.lines.lld;

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
 * Landlord (LLD) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book CRB-LLD-7.2; edit the rule book, not this file.
 */
public final class LandlordClaimRules {
    private LandlordClaimRules() {}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
            Map.entry("RENT_ARREARS", new BigDecimal("0.70")),
            Map.entry("TENANT_DAMAGE", new BigDecimal("1.05")),
            Map.entry("ESCAPE_OF_WATER", new BigDecimal("0.72")),
            Map.entry("LOSS_OF_RENT", new BigDecimal("1.59")),
            Map.entry("STORM", new BigDecimal("1.00"))
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of("ESCAPE_OF_WATER");

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
            Map.entry("RENT_ARREARS", "booking confirmation; invoice for emergency repairs; forensic IT report; medical report"),
            Map.entry("TENANT_DAMAGE", "medical report; police crime reference"),
            Map.entry("ESCAPE_OF_WATER", "tenancy agreement; bank statements for the period; letter of complaint from the third party"),
            Map.entry("LOSS_OF_RENT", "drainage survey; invoice for emergency repairs; medical report"),
            Map.entry("STORM", "medical report; loss adjuster's site report; weather station report for the date")
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual CRB-LLD-7.2). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
            Map.entry("RENT_ARREARS", "Arrange an inspection within 10 working days. Check for a prior claim on the same item within 7 days. Ask the fraud team to review if the policy is under 14 days old."),
            Map.entry("TENANT_DAMAGE", "Do not pay before the 7-day cooling-off for disputed liability. Request the documents again after 90 days, then close as withdrawn."),
            Map.entry("ESCAPE_OF_WATER", "Use the approved supplier panel; out-of-panel repairs capped at 250 GBP. Arrange an inspection within 3 working days. Request the documents again after 30 days, then close as withdrawn."),
            Map.entry("LOSS_OF_RENT", "Ask the fraud team to review if the policy is under 7 days old. Escalate to the claims manager above 7500 GBP."),
            Map.entry("STORM", "Ask the fraud team to review if the policy is under 5 days old. Do not pay before the 7-day cooling-off for disputed liability. Appoint a loss adjuster when the estimate exceeds 21 GBP.")
    );

    static final int REPORTING_WINDOW_DAYS = 30;
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("1000000");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("0.11");

    @Component
    public static class Validator implements LineRules.LineValidator {
        @Override public String lineCode() { return "LLD"; }

        @Override
        public void validate(FnolRequest request) {
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {
                throw new IllegalArgumentException("LLD: unknown loss cause " + request.lossCause());
            }
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {
                throw new IllegalArgumentException("LLD: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {
                throw new IllegalArgumentException("LLD: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }
            // no line-specific checks
        }
    }

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {
        @Override public String lineCode() { return "LLD"; }

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
            return new Reserve("LLD", indemnity, expenses);
        }
    }
}
