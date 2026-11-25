package com.corvane.claims.bureau;

import com.sentinelexchange.sdk.SentinelClient;
import com.sentinelexchange.sdk.model.PriorClaim;
import com.sentinelexchange.sdk.model.SearchRequest;
import com.sentinelexchange.sdk.model.SearchResult;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.time.LocalDate;
import java.util.List;

/**
 * Adapter over the vendored Sentinel Claims Exchange SDK v2 (vendor/sentinel-exchange-sdk). The exchange is an
 * industry fraud bureau reached over SOAP. Name, date of birth and postcode leave Corvane here (DSA-2024-017).
 */
@Component
public class SentinelExchangeAdapter {

    private static final Logger log = LoggerFactory.getLogger(SentinelExchangeAdapter.class);

    private final SentinelClient client;
    private final String memberId;
    private final boolean enabled;

    public SentinelExchangeAdapter(@Value("${claims.bureau.sentinel.endpoint}") String endpoint,
                                   @Value("${claims.bureau.sentinel.member-id}") String memberId,
                                   @Value("${claims.bureau.sentinel.api-key}") String apiKey,
                                   @Value("${claims.bureau.sentinel.enabled:true}") boolean enabled) {
        this.enabled = enabled;
        this.memberId = memberId;
        this.client = enabled ? SentinelClient.builder()
                .endpoint(endpoint)
                .memberId(memberId)
                .credentials(memberId, apiKey)
                .timeout(Duration.ofSeconds(4))
                .maxRetries(1)
                .build() : null;
    }

    /** Prior claims for this person in the last three years across member insurers; 0 when disabled or down. */
    @CircuitBreaker(name = "sentinel", fallbackMethod = "noMatches")
    public int priorClaimsInThreeYears(String fullName, LocalDate dateOfBirth, String postcode) {
        if (!enabled) {
            return 0;
        }
        String[] names = fullName.trim().split("\\s+", 2);
        SearchRequest request = new SearchRequest().withMember(memberId);
        request.forename = names[0];
        request.surname = names.length > 1 ? names[1] : names[0];
        request.dateOfBirth = dateOfBirth;
        request.postcode = postcode;
        request.lookbackYears = 3;
        SearchResult result = client.searchPriorClaims(request);
        List<PriorClaim> priors = result.matches;
        log.info("Sentinel exchange: {} prior claims, risk band {}", priors.size(), result.riskBand);
        return priors.size();
    }

    @SuppressWarnings("unused")
    private int noMatches(String fullName, LocalDate dob, String postcode, Throwable t) {
        log.warn("Sentinel exchange unavailable: {}", t.toString());
        return 0;
    }
}
