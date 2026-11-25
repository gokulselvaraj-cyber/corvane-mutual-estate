package com.corvane.policy.service;

import com.corvane.policy.domain.*;
import com.corvane.policy.events.PolicyEventPublisher;
import com.corvane.policy.ledger.LedgerClient;
import com.corvane.policy.repository.PolicyRepository;
import com.corvane.policy.repository.QuoteRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.*;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

class PolicyServiceTest {

    private final Clock clock = Clock.fixed(Instant.parse("2026-11-16T09:00:00Z"), ZoneOffset.UTC);
    private PolicyRepository policies;
    private QuoteRepository quotes;
    private LedgerClient ledger;
    private PolicyEventPublisher events;
    private PolicyService service;

    @BeforeEach
    void setUp() {
        policies = mock(PolicyRepository.class);
        quotes = mock(QuoteRepository.class);
        ledger = mock(LedgerClient.class);
        events = mock(PolicyEventPublisher.class);
        service = new PolicyService(policies, quotes, ledger, events, clock);
        when(policies.nextPolicySequence()).thenReturn(123456L);
    }

    private Quote quote(String referral, Instant validUntil) {
        PolicyHolder h = new PolicyHolder("PTY000000000001", "Ada Example", LocalDate.of(1985, 3, 2), "LS1 4AP");
        RatingResult r = new RatingResult(new BigDecimal("500.00"), new BigDecimal("60.00"), new BigDecimal("560.00"),
                new BigDecimal("250"), referral, "java");
        return new Quote(ProductLine.MTR, h, r, validUntil);
    }

    @Test
    void bindPostsToLedgerAndPublishes() {
        Quote q = quote(null, clock.instant().plusSeconds(3600));
        when(quotes.findById(q.getId())).thenReturn(Optional.of(q));
        Policy p = service.bind(q.getId(), LocalDate.of(2026, 12, 1), "BRK042");
        assertThat(p.getPolicyNumber()).isEqualTo("MTR000123456");
        assertThat(p.getExpiryDate()).isEqualTo(LocalDate.of(2027, 11, 30));
        verify(ledger).postPremium(p);
        verify(events).policyBound(p, "BRK042");
    }

    @Test
    void referredQuoteCannotBeBound() {
        Quote q = quote("Prior claims above 3", clock.instant().plusSeconds(3600));
        when(quotes.findById(q.getId())).thenReturn(Optional.of(q));
        assertThatThrownBy(() -> service.bind(q.getId(), null, null)).isInstanceOf(QuoteNotBindableException.class);
        verifyNoInteractions(ledger, events);
    }

    @Test
    void expiredQuoteCannotBeBound() {
        Quote q = quote(null, clock.instant().minusSeconds(1));
        when(quotes.findById(q.getId())).thenReturn(Optional.of(q));
        assertThatThrownBy(() -> service.bind(q.getId(), null, null)).hasMessageContaining("expired");
    }
}
