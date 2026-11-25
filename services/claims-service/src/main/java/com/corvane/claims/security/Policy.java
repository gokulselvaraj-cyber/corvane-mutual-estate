package com.corvane.claims.security;

import java.util.Set;

/**
 * An ACCESS policy: which roles may see which claim fields. Not an insurance policy
 * (that is com.corvane.policy.domain.Policy in policy-admin).
 */
public record Policy(String name, Set<String> roles, Set<String> visibleFields) {

    public static final Policy ADJUSTER_VIEW = new Policy("adjuster-view", Set.of("ADJUSTER", "CLAIMS_MANAGER"),
            Set.of("claimNumber", "status", "reserveAmount", "fraudScore", "injuryNotes", "claimantName"));

    public static final Policy CUSTOMER_VIEW = new Policy("customer-view", Set.of("CUSTOMER"),
            Set.of("claimNumber", "status", "paidAmount"));

    public boolean allows(String role, String field) {
        return roles.contains(role) && visibleFields.contains(field);
    }
}
