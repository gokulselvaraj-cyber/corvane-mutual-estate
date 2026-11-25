package com.corvane.policy.service;

import com.corvane.policy.domain.Policy;
import com.corvane.policy.domain.Quote;
import com.corvane.policy.events.PolicyEventPublisher;
import com.corvane.policy.ledger.LedgerClient;
import com.corvane.policy.repository.PolicyRepository;
import com.corvane.policy.repository.QuoteRepository;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Clock;
import java.time.LocalDate;

/** J4 steps 4–6: bind a quote, post the premium to the Oracle ledger, publish policies.bound.v1. */
@Service
public class PolicyService {

    private final PolicyRepository policies;
    private final QuoteRepository quotes;
    private final LedgerClient ledger;
    private final PolicyEventPublisher events;
    private final Clock clock;

    public PolicyService(PolicyRepository policies, QuoteRepository quotes, LedgerClient ledger,
                         PolicyEventPublisher events, Clock clock) {
        this.policies = policies;
        this.quotes = quotes;
        this.ledger = ledger;
        this.events = events;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public Policy find(String policyNumber) {
        return policies.findByPolicyNumber(policyNumber)
                .orElseThrow(() -> new EntityNotFoundException("No policy " + policyNumber));
    }

    @Transactional
    public Policy bind(String quoteId, LocalDate inception, String brokerCode) {
        Quote quote = quotes.findById(quoteId).orElseThrow(() -> new EntityNotFoundException("No quote " + quoteId));
        if (quote.isReferred()) {
            throw new QuoteNotBindableException("Quote " + quoteId + " is referred to an underwriter: " + quote.getReferralReason());
        }
        if (quote.isExpired(clock.instant())) {
            throw new QuoteNotBindableException("Quote " + quoteId + " expired at " + quote.getValidUntil());
        }
        String number = PolicyNumbers.format(quote.getLine(), policies.nextPolicySequence());
        Policy policy = new Policy(number, quote.getLine(), quote.getHolder());
        LocalDate start = inception == null ? LocalDate.now(clock) : inception;
        policy.bind(start, quote.getTotalPremium(), quote.getIptAmount(), "java");
        policies.save(policy);
        quote.markBound(policy.getId());
        ledger.postPremium(policy);
        events.policyBound(policy, brokerCode);
        return policy;
    }
}
