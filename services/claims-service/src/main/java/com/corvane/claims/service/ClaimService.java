package com.corvane.claims.service;

import com.corvane.claims.api.ClaimDtos.ClaimResponse;
import com.corvane.claims.api.ClaimDtos.FnolRequest;
import com.corvane.claims.bureau.SentinelExchangeAdapter;
import com.corvane.claims.client.FraudScoringClient;
import com.corvane.claims.client.PolicyAdminClient;
import com.corvane.claims.client.PolicyAdminClient.PolicyView;
import com.corvane.claims.domain.Claim;
import com.corvane.claims.domain.ClaimParty;
import com.corvane.claims.domain.ClaimStatus;
import com.corvane.claims.events.ClaimEventPublisher;
import com.corvane.claims.lines.LineRules;
import com.corvane.claims.repository.ClaimPartyRepository;
import com.corvane.claims.repository.ClaimRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Journey J1 (FNOL): register -> policy lookup -> coverage -> fraud score -> triage -> save -> publish.
 */
@Service
public class ClaimService {

    private final PolicyAdminClient policyAdmin;
    private final CoverageChecker coverageChecker;
    private final FraudScoringClient fraudScoring;
    private final SentinelExchangeAdapter sentinel;
    private final TriageService triage;
    private final ClaimRepository claims;
    private final ClaimPartyRepository parties;
    private final ClaimEventPublisher events;
    private final LineRules lineRules;

    public ClaimService(PolicyAdminClient policyAdmin, CoverageChecker coverageChecker, FraudScoringClient fraudScoring,
                        SentinelExchangeAdapter sentinel, TriageService triage, ClaimRepository claims,
                        ClaimPartyRepository parties, ClaimEventPublisher events, LineRules lineRules) {
        this.policyAdmin = policyAdmin;
        this.coverageChecker = coverageChecker;
        this.fraudScoring = fraudScoring;
        this.sentinel = sentinel;
        this.triage = triage;
        this.claims = claims;
        this.parties = parties;
        this.events = events;
        this.lineRules = lineRules;
    }

    @Transactional
    public ClaimResponse register(FnolRequest request, String userId) {
        PolicyView policy = policyAdmin.getPolicy(request.policyNumber());
        coverageChecker.check(policy, request);
        lineRules.validate(policy.lineCode(), request);

        Claim claim = Claim.newClaim(String.format("CLM-%09d", claims.nextClaimNumber()),
                policy.policyNumber(), policy.lineCode());
        claim.setIncidentDate(request.incidentDate());
        claim.setLossCause(request.lossCause());
        claim.setDescription(request.description());
        claim.setInjuryNotes(request.injuryNotes());
        claim.setEstimatedAmount(request.estimatedAmount());
        claim.setReserveAmount(lineRules.initialReserve(policy.lineCode(), request).total());
        claim.setRegisteredBy(userId);

        int priorClaims = sentinel.priorClaimsInThreeYears(policy.holderName(), policy.holderDateOfBirth(), policy.postcode());
        double score = fraudScoring.score(claim, policy, priorClaims);
        claim.setFraudScore(score);

        TriageService.Outcome outcome = triage.triage(claim, score);
        claim.setTriageOutcome(outcome.name());
        claim.setStatus(outcome == TriageService.Outcome.AUTO_APPROVE ? ClaimStatus.APPROVED : ClaimStatus.REFERRED);

        claims.save(claim);
        parties.save(ClaimParty.policyholder(claim.getId(), policy.holderName(), policy.holderDateOfBirth(),
                policy.nationalId(), policy.postcode(), policy.email()));
        events.claimRegistered(claim, policy);
        if (outcome == TriageService.Outcome.AUTO_APPROVE) {
            events.claimApproved(claim, claim.getEstimatedAmount(), request.payee(), "AUTO");
        }
        return new ClaimResponse(claim.getId(), claim.getClaimNumber(), claim.getStatus().name(),
                outcome.name(), claim.getReserveAmount(), claim.getRegisteredAt());
    }
}
