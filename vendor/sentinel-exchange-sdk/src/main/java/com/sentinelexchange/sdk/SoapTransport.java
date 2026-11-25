package com.sentinelexchange.sdk;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Base64;

/** Minimal SOAP 1.1 transport over java.net.http. Retries only on HTTP 503 (2.0.3). */
final class SoapTransport implements AutoCloseable {

    private final HttpClient http;
    private final URI endpoint;
    private final String authHeader;
    private final Duration timeout;
    private final int maxRetries;

    SoapTransport(String endpoint, String user, String password, Duration timeout, int maxRetries) {
        this.http = HttpClient.newBuilder().connectTimeout(timeout).build();
        this.endpoint = URI.create(endpoint);
        this.authHeader = "Basic " + Base64.getEncoder().encodeToString((user + ":" + password).getBytes(StandardCharsets.UTF_8));
        this.timeout = timeout;
        this.maxRetries = maxRetries;
    }

    <T> T call(String operation, Object body, Class<T> type) {
        String envelope = XmlCodec.envelope(operation, body);
        for (int attempt = 0; ; attempt++) {
            try {
                HttpResponse<String> r = http.send(HttpRequest.newBuilder(endpoint)
                        .timeout(timeout)
                        .header("Content-Type", "text/xml; charset=utf-8")
                        .header("SOAPAction", "urn:sentinel:claims:" + operation)
                        .header("Authorization", authHeader)
                        .POST(HttpRequest.BodyPublishers.ofString(envelope)).build(), HttpResponse.BodyHandlers.ofString());
                if (r.statusCode() == 503 && attempt < maxRetries) {
                    continue;
                }
                if (r.statusCode() >= 300) {
                    throw new SentinelException(operation + " failed with HTTP " + r.statusCode());
                }
                return XmlCodec.decode(r.body(), type);
            } catch (java.io.IOException e) {
                throw new SentinelException(operation + " transport error: " + e.getMessage());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new SentinelException(operation + " interrupted");
            }
        }
    }

    @Override
    public void close() { /* java.net.http.HttpClient has no close before Java 21 */ }
}
