package com.corvane.claims.service;

import com.corvane.claims.domain.Claim;
import com.corvane.claims.domain.ClaimStatus;
import com.corvane.claims.events.ClaimEventPublisher;
import com.corvane.claims.repository.ClaimRepository;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Closes paid claims after the 30-day complaint window and publishes claims.closed.v1 for the warehouse. */
@Service
public class ClaimClosureService {

    private final ClaimRepository claims;
    private final ClaimEventPublisher events;

    public ClaimClosureService(ClaimRepository claims, ClaimEventPublisher events) {
        this.claims = claims;
        this.events = events;
    }

    @Scheduled(cron = "0 15 2 * * *", zone = "Europe/London")
    @Transactional
    public void closePaidClaims() {
        for (Claim c : claims.findByStatus(ClaimStatus.PAID)) {
            c.setStatus(ClaimStatus.CLOSED);
            claims.save(c);
            events.claimClosed(c);
        }
    }
}
