package com.corvane.claims.service;

import com.corvane.claims.api.ClaimDtos.ApprovalRequest;
import com.corvane.claims.api.ClaimDtos.ClaimResponse;
import com.corvane.claims.domain.Claim;
import com.corvane.claims.domain.ClaimStatus;
import com.corvane.claims.events.ClaimEventPublisher;
import com.corvane.claims.repository.ClaimRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.UUID;

/** Journey J2: an adjuster (portal or mobile adjuster-app) approves a referred claim; payout follows by event. */
@Service
public class ClaimApprovalService {

    private final ClaimRepository claims;
    private final ClaimSettlementCalculator calculator;
    private final ClaimEventPublisher events;

    public ClaimApprovalService(ClaimRepository claims, ClaimSettlementCalculator calculator, ClaimEventPublisher events) {
        this.claims = claims;
        this.calculator = calculator;
        this.events = events;
    }

    @Transactional
    public ClaimResponse approve(UUID claimId, ApprovalRequest request, String adjusterId) {
        Claim claim = claims.findById(claimId).orElseThrow(() -> new IllegalArgumentException("No claim " + claimId));
        if (claim.getStatus() != ClaimStatus.REFERRED) {
            throw new IllegalStateException("Only referred claims can be approved, claim is " + claim.getStatus());
        }
        BigDecimal payable = calculator.payable(claim.getLineCode(), request.approvedAmount(), BigDecimal.ZERO);
        claim.setStatus(ClaimStatus.APPROVED);
        claims.save(claim);
        events.claimApproved(claim, payable, request.payee(), adjusterId);
        return new ClaimResponse(claim.getId(), claim.getClaimNumber(), claim.getStatus().name(),
                claim.getTriageOutcome(), claim.getReserveAmount(), claim.getRegisteredAt());
    }
}
