package com.corvane.claims.client;

import com.corvane.claims.client.PolicyAdminClient.PolicyView;
import com.corvane.claims.domain.Claim;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.Map;

/**
 * Calls fraud-scoring POST /v1/score over plain HTTP/JSON. (contracts/fraud-scoring.proto describes a gRPC
 * interface that was planned in 2024 and never built.)
 * Sends the injury notes so the fraud service's LLM triage can read them.
 */
@Component
public class FraudScoringClient {

    private static final double NEUTRAL_SCORE = 0.5;
    private final RestClient http;

    public FraudScoringClient(@Value("${corvane.fraud-scoring.url}") String baseUrl,
                              @Value("${corvane.fraud-scoring.timeout-ms}") int timeoutMs) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(timeoutMs);
        factory.setReadTimeout(timeoutMs);
        this.http = RestClient.builder().baseUrl(baseUrl).requestFactory(factory).build();
    }

    @CircuitBreaker(name = "fraudScoring", fallbackMethod = "neutral")
    public double score(Claim claim, PolicyView policy, int priorClaims) {
        Map<String, Object> body = Map.of(
                "claim_number", claim.getClaimNumber(),
                "line_code", claim.getLineCode(),
                "loss_cause", claim.getLossCause(),
                "estimated_amount", claim.getEstimatedAmount(),
                "description", claim.getDescription() == null ? "" : claim.getDescription(),
                "injury_notes", claim.getInjuryNotes() == null ? "" : claim.getInjuryNotes(),
                "policy_inception", policy.inceptionDate().toString(),
                "incident_date", claim.getIncidentDate().toString(),
                "prior_claims_3y", priorClaims);
        ScoreResponse response = http.post().uri("/v1/score").body(body).retrieve().body(ScoreResponse.class);
        return response == null ? NEUTRAL_SCORE : response.score();
    }

    @SuppressWarnings("unused")
    private double neutral(Claim claim, PolicyView policy, int priorClaims, Throwable t) {
        return NEUTRAL_SCORE; // fraud-scoring down: neutral score, triage then decides on amount
    }

    public record ScoreResponse(double score, String band, java.util.List<String> reasons) {}
}
