package com.corvane.claims.events;

import com.corvane.claims.domain.ClaimStatus;
import com.corvane.claims.repository.ClaimRepository;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.UUID;

/** End of journey J2: payments-gateway reports the bank settled the payout; mark the claim PAID. */
@Component
public class PaymentSettledListener {

    private final ClaimRepository claims;

    public PaymentSettledListener(ClaimRepository claims) {
        this.claims = claims;
    }

    @KafkaListener(topics = "${claims.topics.payments-settled}", groupId = "claims-service")
    @Transactional
    public void onSettled(ClaimEvents.PaymentSettled event) {
        claims.findById(UUID.fromString(event.claimId())).ifPresent(claim -> {
            claim.setPaidAmount(new BigDecimal(event.amount()));
            claim.setStatus(ClaimStatus.PAID);
            claims.save(claim);
        });
    }
}
