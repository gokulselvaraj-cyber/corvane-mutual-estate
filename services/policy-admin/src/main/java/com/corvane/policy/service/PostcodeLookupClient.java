package com.corvane.policy.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.Locale;
import java.util.Map;

/** External postcode lookup (outside the boundary): normalises and validates UK postcodes. */
@Component
public class PostcodeLookupClient {

    private final RestClient http;

    public PostcodeLookupClient(@Value("${postcode.base-url}") String baseUrl, @Value("${postcode.api-key}") String apiKey) {
        this.http = RestClient.builder().baseUrl(baseUrl).defaultHeader("X-Api-Key", apiKey).build();
    }

    @SuppressWarnings("unchecked")
    public String normalise(String raw) {
        String compact = raw.replace(" ", "").toUpperCase(Locale.UK);
        Map<String, Object> body = http.get().uri("/postcodes/{pc}", compact).retrieve().body(Map.class);
        if (body == null || !Boolean.TRUE.equals(body.get("valid"))) {
            throw new IllegalArgumentException("Unknown postcode " + raw);
        }
        return (String) body.get("formatted");
    }
}
