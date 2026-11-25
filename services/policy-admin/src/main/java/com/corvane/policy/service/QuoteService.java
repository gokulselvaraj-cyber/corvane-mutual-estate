package com.corvane.policy.service;

import com.corvane.policy.api.dto.QuoteRequest;
import com.corvane.policy.domain.*;
import com.corvane.policy.repository.PolicyHolderRepository;
import com.corvane.policy.repository.QuoteRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.Clock;
import java.time.Duration;
import java.time.LocalDate;
import java.time.Period;
import java.util.Map;
import java.util.UUID;

/** J4 step 2: turns a quote request into a priced, stored quote valid for 30 days. */
@Service
public class QuoteService {

    static final Duration QUOTE_VALIDITY = Duration.ofDays(30);

    private final RatingService ratingService;
    private final PostcodeLookupClient postcodes;
    private final PolicyHolderRepository holders;
    private final QuoteRepository quotes;
    private final Clock clock;

    public QuoteService(RatingService ratingService, PostcodeLookupClient postcodes, PolicyHolderRepository holders,
                        QuoteRepository quotes, Clock clock) {
        this.ratingService = ratingService;
        this.postcodes = postcodes;
        this.holders = holders;
        this.quotes = quotes;
        this.clock = clock;
    }

    @Transactional
    public Quote quote(QuoteRequest req) {
        String postcode = postcodes.normalise(req.postcode());
        int age = Period.between(req.dateOfBirth(), LocalDate.now(clock)).getYears();
        PolicyHolder holder = holders.save(new PolicyHolder("PTY" + UUID.randomUUID().toString().substring(0, 12).toUpperCase(),
                req.fullName(), req.dateOfBirth(), postcode));
        RatingInput input = new RatingInput(req.line(), postcode, age, req.sumInsured(),
                req.voluntaryExcess() == null ? BigDecimal.ZERO : req.voluntaryExcess(), req.priorClaims(),
                req.factors() == null ? Map.of() : req.factors());
        RatingResult result = ratingService.rate(input);
        return quotes.save(new Quote(req.line(), holder, result, clock.instant().plus(QUOTE_VALIDITY)));
    }
}
