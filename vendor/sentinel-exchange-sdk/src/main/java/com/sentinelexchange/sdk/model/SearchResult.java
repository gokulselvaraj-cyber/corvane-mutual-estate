package com.sentinelexchange.sdk.model;

import java.util.ArrayList;
import java.util.List;

public class SearchResult {
    public String searchRef;
    public int matchCount;
    public List<PriorClaim> matches = new ArrayList<>();
    /** A (clean) to E (high risk). */
    public String riskBand;

    public boolean hasUndisclosedClaims() { return "D".equals(riskBand) || "E".equals(riskBand); }
}
