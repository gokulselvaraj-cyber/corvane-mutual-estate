package com.corvane.claims.service;

import com.corvane.claims.domain.Claim;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;

class TriageServiceTest {

    private final TriageService triage = new TriageService(new BigDecimal("2500"), 0.72);

    private Claim claim(String line, String amount, String injury) {
        Claim c = Claim.newClaim("CLM-000000001", "MTR-00012345", line);
        c.setEstimatedAmount(new BigDecimal(amount));
        c.setInjuryNotes(injury);
        return c;
    }

    @Test
    void smallMotorClaimIsAutoApproved() {
        assertThat(triage.triage(claim("MTR", "1800", null), 0.10)).isEqualTo(TriageService.Outcome.AUTO_APPROVE);
    }

    @Test
    void limitIsInclusive() {
        assertThat(triage.triage(claim("HOM", "2500", null), 0.10)).isEqualTo(TriageService.Outcome.AUTO_APPROVE);
    }

    @Test
    void overLimitIsReferred() {
        assertThat(triage.triage(claim("HOM", "2500.01", null), 0.10)).isEqualTo(TriageService.Outcome.REFER_ADJUSTER);
    }

    @Test
    void highFraudScoreIsReferredToFraud() {
        assertThat(triage.triage(claim("MTR", "300", null), 0.72)).isEqualTo(TriageService.Outcome.REFER_FRAUD);
    }

    @Test
    void injuryAlwaysGoesToAPerson() {
        assertThat(triage.triage(claim("MTR", "300", "whiplash"), 0.10)).isEqualTo(TriageService.Outcome.REFER_ADJUSTER);
    }

    @Test
    void commercialLinesNeverStraightThrough() {
        assertThat(triage.triage(claim("CYB", "100", null), 0.01)).isEqualTo(TriageService.Outcome.REFER_ADJUSTER);
    }
}
