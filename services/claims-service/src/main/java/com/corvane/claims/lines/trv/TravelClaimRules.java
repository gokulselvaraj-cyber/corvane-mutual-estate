package com.corvane.claims.lines.trv;

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
 * Travel (TRV) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book CRB-TRV-6.2; edit the rule book, not this file.
 */
public final class TravelClaimRules {
    private TravelClaimRules() {}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
            Map.entry("MEDICAL_ABROAD", new BigDecimal("1.02")),
            Map.entry("CANCELLATION", new BigDecimal("1.00")),
            Map.entry("LOST_BAGGAGE", new BigDecimal("0.95")),
            Map.entry("DELAYED_DEPARTURE", new BigDecimal("1.47")),
            Map.entry("PERSONAL_LIABILITY", new BigDecimal("1.41"))
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of("MEDICAL_ABROAD", "DELAYED_DEPARTURE");

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
            Map.entry("MEDICAL_ABROAD", "letter of complaint from the third party; booking confirmation; bank statements for the period; tenancy agreement"),
            Map.entry("CANCELLATION", "proof of purchase or valuation; vet invoice; tenancy agreement; letter of complaint from the third party"),
            Map.entry("LOST_BAGGAGE", "booking confirmation; proof of purchase or valuation; loss adjuster's site report; medical report"),
            Map.entry("DELAYED_DEPARTURE", "witness statements; drainage survey; loss adjuster's site report"),
            Map.entry("PERSONAL_LIABILITY", "photos of the damage; invoice for emergency repairs; vet invoice")
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual CRB-TRV-6.2). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
            Map.entry("MEDICAL_ABROAD", "Check for a prior claim on the same item within 250 days. Instruct a specialist within 10 hours of notification."),
            Map.entry("CANCELLATION", "Request the documents again after 21 days, then close as withdrawn. Ask the fraud team to review if the policy is under 180 days old. Arrange an inspection within 21 working days."),
            Map.entry("LOST_BAGGAGE", "Check for a prior claim on the same item within 21 days. Appoint a loss adjuster when the estimate exceeds 7 GBP. Instruct a specialist within 14 hours of notification."),
            Map.entry("DELAYED_DEPARTURE", "Escalate to the claims manager above 2500 GBP. Ask the fraud team to review if the policy is under 30 days old. Appoint a loss adjuster when the estimate exceeds 90 GBP."),
            Map.entry("PERSONAL_LIABILITY", "Appoint a loss adjuster when the estimate exceeds 7500 GBP. Request the documents again after 60 days, then close as withdrawn.")
    );

    static final int REPORTING_WINDOW_DAYS = 60;
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("250000");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("0.07");

    @Component
    public static class Validator implements LineRules.LineValidator {
        @Override public String lineCode() { return "TRV"; }

        @Override
        public void validate(FnolRequest request) {
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {
                throw new IllegalArgumentException("TRV: unknown loss cause " + request.lossCause());
            }
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {
                throw new IllegalArgumentException("TRV: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {
                throw new IllegalArgumentException("TRV: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }
            if ("MEDICAL_ABROAD".equals(request.lossCause()) && (request.injuryNotes() == null || request.injuryNotes().isBlank())) {
                throw new IllegalArgumentException("TRV: medical claims need treatment notes");
            }
        }
    }

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {
        @Override public String lineCode() { return "TRV"; }

        @Override
        public Reserve initialReserve(FnolRequest request) {
            BigDecimal factor = RESERVE_FACTORS.getOrDefault(request.lossCause(), BigDecimal.ONE);
            BigDecimal indemnity = request.estimatedAmount().multiply(factor).setScale(2, RoundingMode.HALF_UP);
            BigDecimal floor = new BigDecimal("100");
            if (indemnity.compareTo(floor) < 0) {
                indemnity = floor;
            }
            if (ALWAYS_REFER.contains(request.lossCause())) {
                indemnity = indemnity.multiply(new BigDecimal("1.25")).setScale(2, RoundingMode.HALF_UP);
            }
            BigDecimal expenses = indemnity.multiply(EXPENSE_LOADING).setScale(2, RoundingMode.HALF_UP);
            return new Reserve("TRV", indemnity, expenses);
        }
    }
}
