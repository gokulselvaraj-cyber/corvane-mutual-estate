package com.sentinelexchange.sdk.model;

import com.sentinelexchange.sdk.SentinelException;
import java.time.LocalDate;

/** Search subject. At least surname + dateOfBirth, or vehicleRegistration, is required. Default lookback 5 years (2.0). */
public class SearchRequest {
    public String memberId;
    public String surname;
    public String forename;
    public LocalDate dateOfBirth;
    public String nationalId;
    public String postcode;
    public String vehicleRegistration;
    public int lookbackYears = 5;

    public SearchRequest withMember(String m) { this.memberId = m; return this; }

    public void validate() {
        boolean person = surname != null && dateOfBirth != null;
        if (!person && vehicleRegistration == null) {
            throw new SentinelException("surname and dateOfBirth, or vehicleRegistration, are required");
        }
        if (lookbackYears < 1 || lookbackYears > 10) {
            throw new SentinelException("lookbackYears must be 1..10");
        }
    }
}
