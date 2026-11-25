package com.corvane.policy.events;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.OffsetDateTime;

/**
 * Payload of policies.bound.v1 (contracts/avro/policy-bound.avsc).
 * Consumers: broker-commissions (BoundPolicyConsumer) and notifications (PolicyBoundHandler, welcome email).
 * Carries the policyholder's name and email (personal data).
 */
public record PolicyBoundEvent(String policyNumber, String lineCode, String partyRef, String holderName,
                               String holderEmail, String brokerCode, BigDecimal annualPremium, BigDecimal iptAmount,
                               String currency, LocalDate inceptionDate, String premiumEngine, OffsetDateTime boundAt) {
}
