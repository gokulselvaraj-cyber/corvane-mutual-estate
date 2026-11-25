package com.corvane.policy.service;

import com.corvane.policy.domain.Policy;
import com.corvane.policy.domain.PolicyStatus;
import com.corvane.policy.domain.RatingInput;
import com.corvane.policy.domain.RatingResult;
import com.corvane.policy.repository.PolicyRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.Clock;
import java.time.LocalDate;
import java.time.Period;
import java.util.List;
import java.util.Map;

/**
 * Finds policies expiring in the renewal window and re-prices them.
 *
 * <p>TODO(POL-1184): send the renewal invitation. The priced renewal is only logged; no event is published and no
 * email is sent, so customers are not told about renewals by this service.</p>
 */
@Service
public class RenewalService {

    private static final Logger log = LoggerFactory.getLogger(RenewalService.class);

    private final PolicyRepository policies;
    private final RatingService rating;
    private final Clock clock;
    private final int windowDays;

    public RenewalService(PolicyRepository policies, RatingService rating, Clock clock,
                          @Value("${policy.renewals.window-days}") int windowDays) {
        this.policies = policies;
        this.rating = rating;
        this.clock = clock;
        this.windowDays = windowDays;
    }

    @Scheduled(cron = "0 0 6 * * MON-FRI", zone = "Europe/London")
    @Transactional
    public int priceDueRenewals() {
        LocalDate today = LocalDate.now(clock);
        List<Policy> due = policies.findExpiring(PolicyStatus.BOUND, today, today.plusDays(windowDays));
        for (Policy p : due) {
            int age = Period.between(p.getHolder().getDateOfBirth(), today).getYears();
            RatingResult r = rating.rate(new RatingInput(p.getLine(), p.getHolder().getPostcode(), age,
                    p.getAnnualPremium().multiply(BigDecimal.valueOf(40)), p.getVoluntaryExcess(), 0, Map.of()));
            p.markRenewalDue();
            log.info("Renewal priced policy={} old={} new={} engine={}", p.getPolicyNumber(), p.getAnnualPremium(),
                    r.totalPremium(), r.engine());
            // TODO(POL-1184): publish policies.renewal-offered.v1 and email the holder.
        }
        return due.size();
    }
}
