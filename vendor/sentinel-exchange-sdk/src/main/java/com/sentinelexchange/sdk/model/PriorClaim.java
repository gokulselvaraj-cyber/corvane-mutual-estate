package com.sentinelexchange.sdk.model;

import java.math.BigDecimal;
import java.time.LocalDate;

public class PriorClaim {
    public String exchangeRef;
    public String insurerCode;
    public String lossType;
    public LocalDate lossDate;
    public BigDecimal settledAmount;
    public ClaimStatus status;
    public int matchScore; // 0..100
}
