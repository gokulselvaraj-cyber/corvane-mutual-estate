package com.corvane.claims.lines.mtr;

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
 * Motor (MTR) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book CRB-MTR-3.2; edit the rule book, not this file.
 */
public final class MotorClaimRules {
    private MotorClaimRules() {}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
            Map.entry("REAR_END_COLLISION", new BigDecimal("0.81")),
            Map.entry("THEFT_OF_VEHICLE", new BigDecimal("0.81")),
            Map.entry("WINDSCREEN", new BigDecimal("1.00")),
            Map.entry("FIRE", new BigDecimal("1.53")),
            Map.entry("VANDALISM", new BigDecimal("1.10")),
            Map.entry("FLOOD_DAMAGE", new BigDecimal("0.92")),
            Map.entry("HIT_AND_RUN", new BigDecimal("0.61"))
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of("FLOOD_DAMAGE");

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
            Map.entry("REAR_END_COLLISION", "weather station report for the date; bank statements for the period"),
            Map.entry("THEFT_OF_VEHICLE", "tenancy agreement; repair estimate from an approved repairer; proof of purchase or valuation"),
            Map.entry("WINDSCREEN", "medical report; carrier's bill of lading"),
            Map.entry("FIRE", "medical report; vet invoice; bank statements for the period; police crime reference"),
            Map.entry("VANDALISM", "proof of purchase or valuation; medical report; forensic IT report"),
            Map.entry("FLOOD_DAMAGE", "photos of the damage; letter of complaint from the third party; drainage survey; repair estimate from an approved repairer"),
            Map.entry("HIT_AND_RUN", "carrier's bill of lading; booking confirmation; vet invoice")
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual CRB-MTR-3.2). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
            Map.entry("REAR_END_COLLISION", "Arrange an inspection within 30 working days. Ask the fraud team to review if the policy is under 90 days old."),
            Map.entry("THEFT_OF_VEHICLE", "Do not pay before the 90-day cooling-off for disputed liability. Use the approved supplier panel; out-of-panel repairs capped at 15000 GBP. Check for a prior claim on the same item within 60 days."),
            Map.entry("WINDSCREEN", "Appoint a loss adjuster when the estimate exceeds 30 GBP. Instruct a specialist within 60 hours of notification."),
            Map.entry("FIRE", "Ask the fraud team to review if the policy is under 10 days old. Arrange an inspection within 2500 working days."),
            Map.entry("VANDALISM", "Instruct a specialist within 10 hours of notification. Use the approved supplier panel; out-of-panel repairs capped at 15000 GBP."),
            Map.entry("FLOOD_DAMAGE", "Arrange an inspection within 14 working days. Escalate to the claims manager above 500 GBP."),
            Map.entry("HIT_AND_RUN", "Use the approved supplier panel; out-of-panel repairs capped at 15000 GBP. Ask the fraud team to review if the policy is under 180 days old.")
    );

    static final int REPORTING_WINDOW_DAYS = 60;
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("250000");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("0.14");

    @Component
    public static class Validator implements LineRules.LineValidator {
        @Override public String lineCode() { return "MTR"; }

        @Override
        public void validate(FnolRequest request) {
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {
                throw new IllegalArgumentException("MTR: unknown loss cause " + request.lossCause());
            }
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {
                throw new IllegalArgumentException("MTR: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {
                throw new IllegalArgumentException("MTR: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }
            if (request.incidentPostcode() == null) {
                throw new IllegalArgumentException("MTR: incident postcode is required for motor claims");
            }
        }
    }

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {
        @Override public String lineCode() { return "MTR"; }

        @Override
        public Reserve initialReserve(FnolRequest request) {
            BigDecimal factor = RESERVE_FACTORS.getOrDefault(request.lossCause(), BigDecimal.ONE);
            BigDecimal indemnity = request.estimatedAmount().multiply(factor).setScale(2, RoundingMode.HALF_UP);
            BigDecimal floor = new BigDecimal("1000");
            if (indemnity.compareTo(floor) < 0) {
                indemnity = floor;
            }
            if (ALWAYS_REFER.contains(request.lossCause())) {
                indemnity = indemnity.multiply(new BigDecimal("1.31")).setScale(2, RoundingMode.HALF_UP);
            }
            BigDecimal expenses = indemnity.multiply(EXPENSE_LOADING).setScale(2, RoundingMode.HALF_UP);
            return new Reserve("MTR", indemnity, expenses);
        }
    }
}
