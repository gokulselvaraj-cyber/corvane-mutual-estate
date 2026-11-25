package com.corvane.claims.domain;

/** Lifecycle of a claim. Mirrors CLM-STATUS in copybook CLMREC (R=REGISTERED, F=REFERRED, A=APPROVED, P=PAID, C=CLOSED). */
public enum ClaimStatus { REGISTERED, REFERRED, APPROVED, PAID, CLOSED, DECLINED }
