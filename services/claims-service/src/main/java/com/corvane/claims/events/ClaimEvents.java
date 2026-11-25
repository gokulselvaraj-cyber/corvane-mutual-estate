package com.corvane.claims.events;

/** Event payloads; field names match contracts/avro/*.avsc. */
public final class ClaimEvents {
    private ClaimEvents() {}

    /** claims.registered.v1: notifications emails the claimant, fraud-scoring re-scores with the full narrative. */
    public record ClaimRegistered(String claimId, String claimNumber, String policyNumber, String lineCode,
                                  String status, String triageOutcome, String claimantName, String claimantEmail,
                                  String claimantMobile, String postcode, String lossDate, String reportedDate,
                                  String policyStartDate, String claimedAmount, String currency, String lossCause,
                                  String narrative, String injuryNotes, String occurredAt) {}

    /** claims.approved.v1: payments-gateway pays the payee. Carries bank details (personal data). */
    public record ClaimApproved(String claimId, String claimNumber, int approvalSeq, String policyNumber,
                                String lineCode, String payeeName, String payeeSortCode, String payeeAccount,
                                String settlementAmount, String currency, String approvedBy, String occurredAt) {}

    public record ClaimClosed(String claimId, String claimNumber, String lineCode, String paidAmount,
                              String occurredAt) {}

    /** payments.settled.v1, published by payments-gateway (Go) and read by PaymentSettledListener. */
    public record PaymentSettled(String claimId, String paymentRef, String amount, String currency,
                                 String settledAt) {}
}
