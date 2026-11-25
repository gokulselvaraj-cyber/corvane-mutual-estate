package com.corvane.claims.lines.pin;

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
 * ProfessionalIndemnity (PIN) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book CRB-PIN-7.0; edit the rule book, not this file.
 */
public final class ProfessionalIndemnityClaimRules {
    private ProfessionalIndemnityClaimRules() {}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
            Map.entry("NEGLIGENT_ADVICE", new BigDecimal("1.02")),
            Map.entry("BREACH_OF_DUTY", new BigDecimal("1.46")),
            Map.entry("LOSS_OF_DOCUMENTS", new BigDecimal("1.52")),
            Map.entry("DEFAMATION", new BigDecimal("0.62"))
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of("NEGLIGENT_ADVICE");

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
            Map.entry("NEGLIGENT_ADVICE", "invoice for emergency repairs; proof of purchase or valuation; tenancy agreement"),
            Map.entry("BREACH_OF_DUTY", "forensic IT report; carrier's bill of lading"),
            Map.entry("LOSS_OF_DOCUMENTS", "vet invoice; forensic IT report; loss adjuster's site report"),
            Map.entry("DEFAMATION", "carrier's bill of lading; proof of purchase or valuation")
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual CRB-PIN-7.0). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
            Map.entry("NEGLIGENT_ADVICE", "Check for a prior claim on the same item within 14 days. Appoint a loss adjuster when the estimate exceeds 7500 GBP. Arrange an inspection within 500 working days."),
            Map.entry("BREACH_OF_DUTY", "Do not pay before the 7-day cooling-off for disputed liability. Escalate to the claims manager above 2500 GBP. Instruct a specialist within 1000 hours of notification."),
            Map.entry("LOSS_OF_DOCUMENTS", "Do not pay before the 14-day cooling-off for disputed liability. Check for a prior claim on the same item within 180 days."),
            Map.entry("DEFAMATION", "Instruct a specialist within 7 hours of notification. Request the documents again after 90 days, then close as withdrawn. Ask the fraud team to review if the policy is under 14 days old.")
    );

    static final int REPORTING_WINDOW_DAYS = 90;
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("1000000");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("0.16");

    @Component
    public static class Validator implements LineRules.LineValidator {
        @Override public String lineCode() { return "PIN"; }

        @Override
        public void validate(FnolRequest request) {
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {
                throw new IllegalArgumentException("PIN: unknown loss cause " + request.lossCause());
            }
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {
                throw new IllegalArgumentException("PIN: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {
                throw new IllegalArgumentException("PIN: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }
            // no line-specific checks
        }
    }

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {
        @Override public String lineCode() { return "PIN"; }

        @Override
        public Reserve initialReserve(FnolRequest request) {
            BigDecimal factor = RESERVE_FACTORS.getOrDefault(request.lossCause(), BigDecimal.ONE);
            BigDecimal indemnity = request.estimatedAmount().multiply(factor).setScale(2, RoundingMode.HALF_UP);
            BigDecimal floor = new BigDecimal("250");
            if (indemnity.compareTo(floor) < 0) {
                indemnity = floor;
            }
            if (ALWAYS_REFER.contains(request.lossCause())) {
                indemnity = indemnity.multiply(new BigDecimal("1.39")).setScale(2, RoundingMode.HALF_UP);
            }
            BigDecimal expenses = indemnity.multiply(EXPENSE_LOADING).setScale(2, RoundingMode.HALF_UP);
            return new Reserve("PIN", indemnity, expenses);
        }
    }
}
