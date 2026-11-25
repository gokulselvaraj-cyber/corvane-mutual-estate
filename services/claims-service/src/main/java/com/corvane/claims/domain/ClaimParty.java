package com.corvane.claims.domain;

import jakarta.persistence.*;
import java.time.LocalDate;
import java.util.UUID;

/**
 * The policyholder (and any third party) on a claim. Table claims.claim_party, role 'policyholder' or 'third_party'.
 * Same real-world person as PolicyHolder in policy-admin, INSURED in COBOL POLREC and PARTY in the Oracle ledger.
 */
@Entity
@Table(name = "claim_party", schema = "claims")
public class ClaimParty {
    @Id private UUID id;
    @Column(name = "claim_id") private UUID claimId;
    private String role;
    @Column(name = "full_name") private String fullName;
    @Column(name = "date_of_birth") private LocalDate dateOfBirth;
    /** UK National Insurance number or US SSN, stored encrypted at rest by the DB (pgcrypto). */
    @Column(name = "national_id") private String nationalId;
    private String postcode;
    private String email;

    protected ClaimParty() {}

    public static ClaimParty policyholder(UUID claimId, String name, LocalDate dob, String nationalId, String postcode, String email) {
        ClaimParty p = new ClaimParty();
        p.id = UUID.randomUUID();
        p.claimId = claimId;
        p.role = "policyholder";
        p.fullName = name;
        p.dateOfBirth = dob;
        p.nationalId = nationalId;
        p.postcode = postcode;
        p.email = email;
        return p;
    }

    public String getFullName() { return fullName; }
    public LocalDate getDateOfBirth() { return dateOfBirth; }
    public String getPostcode() { return postcode; }
    public String getEmail() { return email; }
}
