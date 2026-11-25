package com.corvane.claims.service;

import com.corvane.claims.api.ClaimDtos.FnolRequest;
import com.corvane.claims.client.PolicyAdminClient.PolicyView;
import org.springframework.stereotype.Component;

/** Rejects a claim when the policy was not in force on the incident date or the loss cause is excluded. */
@Component
public class CoverageChecker {

    public void check(PolicyView policy, FnolRequest request) {
        if (!"IN_FORCE".equals(policy.status()) && !"LAPSED_GRACE".equals(policy.status())) {
            throw new CoverageException("Policy " + policy.policyNumber() + " is " + policy.status());
        }
        if (request.incidentDate().isBefore(policy.inceptionDate()) || request.incidentDate().isAfter(policy.expiryDate())) {
            throw new CoverageException("Incident date outside the period of cover");
        }
        if (policy.exclusions().contains(request.lossCause())) {
            throw new CoverageException("Loss cause " + request.lossCause() + " is excluded on this policy");
        }
    }

    public static class CoverageException extends RuntimeException {
        public CoverageException(String message) { super(message); }
    }
}
