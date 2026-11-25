package com.corvane.claims.events;

import com.corvane.claims.api.ClaimDtos.PayeeDetails;
import com.corvane.claims.client.PolicyAdminClient.PolicyView;
import com.corvane.claims.domain.Claim;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

/** Publishes claim events (schemas in contracts/avro). Key = claim id. */
@Component
public class ClaimEventPublisher {

    private final KafkaTemplate<String, Object> kafka;
    private final String registeredTopic;
    private final String approvedTopic;
    private final String closedTopic;

    public ClaimEventPublisher(KafkaTemplate<String, Object> kafka,
                               @Value("${claims.topics.registered}") String registeredTopic,
                               @Value("${claims.topics.approved}") String approvedTopic,
                               @Value("${claims.topics.closed}") String closedTopic) {
        this.kafka = kafka;
        this.registeredTopic = registeredTopic;
        this.approvedTopic = approvedTopic;
        this.closedTopic = closedTopic;
    }

    /** claims.registered.v1, read by notifications (email) and fraud-scoring (model feedback). */
    public void claimRegistered(Claim claim, PolicyView policy) {
        kafka.send(registeredTopic, claim.getId().toString(), new ClaimEvents.ClaimRegistered(
                claim.getId().toString(), claim.getClaimNumber(), claim.getPolicyNumber(), claim.getLineCode(),
                claim.getStatus().name(), claim.getTriageOutcome(), policy.holderName(), policy.email(), null,
                policy.postcode(), String.valueOf(claim.getIncidentDate()), String.valueOf(claim.getRegisteredAt().toLocalDate()),
                String.valueOf(policy.inceptionDate()), claim.getEstimatedAmount().toPlainString(), "GBP",
                claim.getLossCause(), claim.getDescription(), claim.getInjuryNotes(), OffsetDateTime.now().toString()));
    }

    /** claims.approved.v1, read by payments-gateway ApprovedClaimConsumer. */
    public void claimApproved(Claim claim, BigDecimal payable, PayeeDetails payee, String approvedBy) {
        kafka.send(approvedTopic, claim.getId().toString(), new ClaimEvents.ClaimApproved(
                claim.getId().toString(), claim.getClaimNumber(), 1, claim.getPolicyNumber(), claim.getLineCode(),
                payee.name(), payee.sortCode(), payee.account(), payable.toPlainString(), "GBP", approvedBy,
                OffsetDateTime.now().toString()));
    }

    /** claims.closed.v1, read by warehouse-loader. */
    public void claimClosed(Claim claim) {
        kafka.send(closedTopic, claim.getId().toString(), new ClaimEvents.ClaimClosed(
                claim.getId().toString(), claim.getClaimNumber(), claim.getLineCode(),
                String.valueOf(claim.getPaidAmount()), OffsetDateTime.now().toString()));
    }
}
