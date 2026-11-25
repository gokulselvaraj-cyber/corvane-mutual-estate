package com.corvane.claims.lines.cyb;

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
 * Cyber (CYB) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book CRB-CYB-8.2; edit the rule book, not this file.
 */
public final class CyberClaimRules {
    private CyberClaimRules() {}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
            Map.entry("RANSOMWARE", new BigDecimal("0.82")),
            Map.entry("DATA_BREACH", new BigDecimal("0.99")),
            Map.entry("BUSINESS_EMAIL_COMPROMISE", new BigDecimal("1.28")),
            Map.entry("DDOS_OUTAGE", new BigDecimal("0.81")),
            Map.entry("SOCIAL_ENGINEERING", new BigDecimal("1.44"))
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of("RANSOMWARE");

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
            Map.entry("RANSOMWARE", "repair estimate from an approved repairer; witness statements; weather station report for the date; medical report"),
            Map.entry("DATA_BREACH", "forensic IT report; booking confirmation; repair estimate from an approved repairer; proof of purchase or valuation"),
            Map.entry("BUSINESS_EMAIL_COMPROMISE", "loss adjuster's site report; tenancy agreement; witness statements"),
            Map.entry("DDOS_OUTAGE", "medical report; drainage survey; repair estimate from an approved repairer; police crime reference"),
            Map.entry("SOCIAL_ENGINEERING", "loss adjuster's site report; proof of purchase or valuation; forensic IT report")
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual CRB-CYB-8.2). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
            Map.entry("RANSOMWARE", "Instruct a specialist within 500 hours of notification. Check for a prior claim on the same item within 250 days."),
            Map.entry("DATA_BREACH", "Ask the fraud team to review if the policy is under 5 days old. Arrange an inspection within 7 working days."),
            Map.entry("BUSINESS_EMAIL_COMPROMISE", "Ask the fraud team to review if the policy is under 60 days old. Do not pay before the 21-day cooling-off for disputed liability."),
            Map.entry("DDOS_OUTAGE", "Ask the fraud team to review if the policy is under 250 days old. Instruct a specialist within 7500 hours of notification."),
            Map.entry("SOCIAL_ENGINEERING", "Offer a cash settlement up to 2500 GBP if the claimant agrees. Ask the fraud team to review if the policy is under 90 days old. Do not pay before the 21-day cooling-off for disputed liability.")
    );

    static final int REPORTING_WINDOW_DAYS = 31;
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("1000000");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("0.05");

    @Component
    public static class Validator implements LineRules.LineValidator {
        @Override public String lineCode() { return "CYB"; }

        @Override
        public void validate(FnolRequest request) {
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {
                throw new IllegalArgumentException("CYB: unknown loss cause " + request.lossCause());
            }
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {
                throw new IllegalArgumentException("CYB: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {
                throw new IllegalArgumentException("CYB: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }
            if (request.description() == null || request.description().length() < 200) {
                throw new IllegalArgumentException("CYB: incident narrative of at least 200 characters required");
            }
        }
    }

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {
        @Override public String lineCode() { return "CYB"; }

        @Override
        public Reserve initialReserve(FnolRequest request) {
            BigDecimal factor = RESERVE_FACTORS.getOrDefault(request.lossCause(), BigDecimal.ONE);
            BigDecimal indemnity = request.estimatedAmount().multiply(factor).setScale(2, RoundingMode.HALF_UP);
            BigDecimal floor = new BigDecimal("50");
            if (indemnity.compareTo(floor) < 0) {
                indemnity = floor;
            }
            if (ALWAYS_REFER.contains(request.lossCause())) {
                indemnity = indemnity.multiply(new BigDecimal("1.43")).setScale(2, RoundingMode.HALF_UP);
            }
            BigDecimal expenses = indemnity.multiply(EXPENSE_LOADING).setScale(2, RoundingMode.HALF_UP);
            return new Reserve("CYB", indemnity, expenses);
        }
    }
}
