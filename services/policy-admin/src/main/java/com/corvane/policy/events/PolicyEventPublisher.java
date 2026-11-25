package com.corvane.policy.events;

import com.corvane.policy.domain.Policy;
import java.time.OffsetDateTime;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class PolicyEventPublisher {

    private final KafkaTemplate<String, PolicyBoundEvent> kafka;
    private final String boundTopic;

    public PolicyEventPublisher(KafkaTemplate<String, PolicyBoundEvent> kafka,
                                @Value("${policy.topics.bound}") String boundTopic) {
        this.kafka = kafka;
        this.boundTopic = boundTopic;
    }

    /** Keyed by policy number so all events of one policy land on one partition. */
    public void policyBound(Policy p, String brokerCode) {
        kafka.send(boundTopic, p.getPolicyNumber(), new PolicyBoundEvent(p.getPolicyNumber(), p.getLine().name(),
                p.getHolder().getPartyRef(), p.getHolder().getFullName(), p.getHolder().getEmail(), brokerCode,
                p.getAnnualPremium(), p.getIptAmount(), p.getCurrency(), p.getInceptionDate(), p.getPremiumEngine(),
                OffsetDateTime.now()));
    }
}
