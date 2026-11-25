package com.corvane.claims.api;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

/** Request and response shapes of the claims API (contracts/claims.openapi.yaml 2.3.0). */
public final class ClaimDtos {
    private ClaimDtos() {}

    public record FnolRequest(
            @NotBlank @Pattern(regexp = "[A-Z]{3}-\\d{8}") String policyNumber,
            @NotNull LocalDate incidentDate,
            @NotBlank String lossCause,
            @Size(max = 4000) String description,
            @Size(max = 4000) String injuryNotes,
            @NotNull @PositiveOrZero BigDecimal estimatedAmount,
            String incidentPostcode,
            UUID draftId,
            PayeeDetails payee) {}

    /** Bank details of whoever is paid; carried on claims.approved.v1 to payments-gateway (personal data). */
    public record PayeeDetails(String name, String sortCode, String account) {}

    public record ClaimResponse(UUID claimId, String claimNumber, String status, String triageOutcome,
                                BigDecimal reserveAmount, OffsetDateTime registeredAt) {}

    public record DraftRequest(String policyNumber) {}
    public record DraftResponse(UUID draftId, OffsetDateTime expiresAt) {}
    public record PhotoResponse(UUID draftId, String objectName, long bytes) {}

    public record ApprovalRequest(@NotNull BigDecimal approvedAmount, String note, @NotNull PayeeDetails payee) {}

    public record ClaimSummaryDto(UUID claimId, String claimNumber, String policyNumber, String lineCode,
                                  String status, String claimantName, LocalDate dateOfBirth,
                                  BigDecimal reserveAmount, BigDecimal paidAmount, Double fraudScore,
                                  List<String> notes) {
        public String toCsvRow() {
            return String.join(",", String.valueOf(claimId), policyNumber, lineCode, status,
                    claimantName, String.valueOf(dateOfBirth), String.valueOf(reserveAmount));
        }
    }
}
