package com.corvane.claims.service;

import com.corvane.claims.domain.Claim;
import com.corvane.claims.domain.ClaimStatus;
import com.corvane.claims.repository.ClaimRepository;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

/**
 * Puts referred claims into adjuster queues. Queue by line and size: commercial lines (MAR, CPR, PLB, PIN, CYB)
 * go to the specialist desk; personal lines over 15,000 GBP go to senior adjusters; the rest to the general pool.
 * Fraud referrals (triage outcome REFER_FRAUD) go to the counter-fraud unit whatever the amount.
 */
@Service
public class AdjusterAssignmentService {

    static final BigDecimal SENIOR_THRESHOLD = new BigDecimal("15000");
    static final Map<String, String> SPECIALIST_DESKS = Map.of(
            "MAR", "marine-desk", "CPR", "commercial-property-desk", "PLB", "liability-desk",
            "PIN", "liability-desk", "CYB", "cyber-response-desk");

    private final ClaimRepository claims;

    public AdjusterAssignmentService(ClaimRepository claims) {
        this.claims = claims;
    }

    public String queueFor(Claim claim) {
        if ("REFER_FRAUD".equals(claim.getTriageOutcome())) {
            return "counter-fraud-unit";
        }
        String desk = SPECIALIST_DESKS.get(claim.getLineCode());
        if (desk != null) {
            return desk;
        }
        return claim.getEstimatedAmount().compareTo(SENIOR_THRESHOLD) > 0 ? "senior-adjusters" : "general-pool";
    }

    /** Every 10 minutes, Mon-Sat 07:00-20:00 UK time (claims ops hours). */
    @Scheduled(cron = "0 */10 7-19 * * MON-SAT", zone = "Europe/London")
    public void assignReferred() {
        List<Claim> referred = claims.findByStatus(ClaimStatus.REFERRED);
        referred.forEach(c -> c.setTriageOutcome(c.getTriageOutcome() + "@" + queueFor(c)));
        claims.saveAll(referred);
    }
}
