package com.sentinelexchange.sdk;

import com.sentinelexchange.sdk.model.ClaimStatus;
import com.sentinelexchange.sdk.model.SearchRequest;
import com.sentinelexchange.sdk.model.SearchResult;

import java.time.Duration;
import java.util.List;

/** Entry point of the Sentinel Claims Exchange SDK. Thread-safe; create one per application. */
public final class SentinelClient implements AutoCloseable {

    public static final String DEFAULT_ENDPOINT = "https://soap.sentinel-exchange.example/ClaimsExchange";

    private final SoapTransport transport;
    private final String memberId;

    private SentinelClient(Builder b) {
        this.memberId = b.memberId;
        this.transport = new SoapTransport(b.endpoint, b.username, b.password, b.timeout, b.maxRetries);
    }

    public static Builder builder() { return new Builder(); }

    /** Since 2.0 (was searchClaims in 1.x). Returns prior claims for the subject across member insurers. */
    public SearchResult searchPriorClaims(SearchRequest request) {
        if (request.memberId == null) {
            request.withMember(memberId);
        }
        request.validate();
        return transport.call("SearchPriorClaims", request, SearchResult.class);
    }

    public void updateClaimStatus(String exchangeRef, ClaimStatus status) {
        transport.call("UpdateClaimStatus", new Object[] {memberId, exchangeRef, status.name()}, Void.class);
    }

    public List<String> supportedLossTypes() {
        return List.of("MOTOR_ACCIDENT", "MOTOR_THEFT", "ESCAPE_OF_WATER", "FIRE", "THEFT", "STORM", "LIABILITY", "TRAVEL_MEDICAL");
    }

    @Override
    public void close() { transport.close(); }

    public static final class Builder {
        private String endpoint = DEFAULT_ENDPOINT;
        private String memberId;
        private String username;
        private String password;
        private Duration timeout = Duration.ofSeconds(10);
        private int maxRetries = 2;

        public Builder endpoint(String e) { this.endpoint = e; return this; }
        public Builder memberId(String m) { this.memberId = m; return this; }
        public Builder credentials(String user, String password) { this.username = user; this.password = password; return this; }
        public Builder timeout(Duration t) { this.timeout = t; return this; }
        public Builder maxRetries(int r) { this.maxRetries = r; return this; }

        public SentinelClient build() {
            if (memberId == null || username == null) {
                throw new SentinelException("memberId and credentials are required");
            }
            return new SentinelClient(this);
        }
    }
}
