package com.corvane.claims.service;

import com.corvane.claims.domain.Claim;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.Set;

/**
 * Decides whether a new claim is paid straight through or referred to an adjuster.
 * Rule: auto-approve when the estimate is at or under the limit, the fraud score is under the refer score,
 * and the line allows straight-through processing.
 */
@Service
public class TriageService {

    /** Code default, GBP. Overridden per environment by claims.triage.auto-approve-limit. */
    public static final BigDecimal DEFAULT_AUTO_APPROVE_LIMIT = new BigDecimal("2500");

    private static final Set<String> NEVER_STRAIGHT_THROUGH = Set.of("MAR", "CPR", "PLB", "PIN", "CYB");

    public enum Outcome { AUTO_APPROVE, REFER_ADJUSTER, REFER_FRAUD }

    private final BigDecimal autoApproveLimit;
    private final double referFraudScore;

    public TriageService(@Value("${claims.triage.auto-approve-limit:2500}") BigDecimal autoApproveLimit,
                         @Value("${claims.triage.refer-fraud-score:0.72}") double referFraudScore) {
        this.autoApproveLimit = autoApproveLimit == null ? DEFAULT_AUTO_APPROVE_LIMIT : autoApproveLimit;
        this.referFraudScore = referFraudScore;
    }

    public Outcome triage(Claim claim, double fraudScore) {
        if (fraudScore >= referFraudScore) {
            return Outcome.REFER_FRAUD;
        }
        if (NEVER_STRAIGHT_THROUGH.contains(claim.getLineCode())) {
            return Outcome.REFER_ADJUSTER;
        }
        if (claim.getInjuryNotes() != null && !claim.getInjuryNotes().isBlank()) {
            return Outcome.REFER_ADJUSTER; // any injury goes to a person
        }
        return claim.getEstimatedAmount().compareTo(autoApproveLimit) <= 0 ? Outcome.AUTO_APPROVE : Outcome.REFER_ADJUSTER;
    }

    public BigDecimal autoApproveLimit() { return autoApproveLimit; }
}
