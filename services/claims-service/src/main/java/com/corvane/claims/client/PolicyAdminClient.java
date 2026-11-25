package com.corvane.claims.client;

import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.LocalDate;
import java.util.List;

/** HTTP client for policy-admin GET /v1/policies/{policyNumber}. */
@Component
public class PolicyAdminClient {

    private final RestClient http;

    public PolicyAdminClient(RestClient.Builder builder, @Value("${corvane.policy-admin.url}") String baseUrl) {
        this.http = builder.baseUrl(baseUrl).build();
    }

    @Retry(name = "policyAdmin")
    @CircuitBreaker(name = "policyAdmin")
    public PolicyView getPolicy(String policyNumber) {
        return http.get().uri("/v1/policies/{policyNumber}", policyNumber).retrieve().body(PolicyView.class);
    }

    /** The parts of policy-admin's Policy resource claims needs. holder* fields come from PolicyHolder. */
    public record PolicyView(String policyNumber, String lineCode, String status, LocalDate inceptionDate,
                             LocalDate expiryDate, List<String> exclusions, String holderName,
                             LocalDate holderDateOfBirth, String nationalId, String postcode, String email,
                             String region) {}
}
