package com.corvane.policy.domain;

import jakarta.persistence.*;
import java.time.LocalDate;

/**
 * The person or business that holds a policy.
 *
 * <p>Naming across the estate: the mainframe calls this the INSURED (copybook POLREC, INSURED-NAME), the Oracle
 * ledger calls it a PARTY, the customer portal calls it a Customer and claims-service stores it as the
 * policyholder row of claims.claim_party. They are the same real-world entity, joined on {@code partyRef}.</p>
 */
@Entity
@Table(name = "policy_holder")
public class PolicyHolder {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "party_ref", nullable = false, unique = true)
    private String partyRef;

    @Column(name = "full_name", nullable = false)
    private String fullName;

    @Column(name = "date_of_birth")
    private LocalDate dateOfBirth;

    /** UK National Insurance number or US SSN. Personal data: masked in every log line. */
    @Column(name = "national_id")
    private String nationalId;

    private String email;

    @Column(name = "address_line1")
    private String addressLine1;

    private String postcode;
    private String country = "GB";

    protected PolicyHolder() { }

    public PolicyHolder(String partyRef, String fullName, LocalDate dateOfBirth, String postcode) {
        this.partyRef = partyRef;
        this.fullName = fullName;
        this.dateOfBirth = dateOfBirth;
        this.postcode = postcode;
    }

    public Long getId() { return id; }
    public String getPartyRef() { return partyRef; }
    public String getFullName() { return fullName; }
    public LocalDate getDateOfBirth() { return dateOfBirth; }
    public String getNationalId() { return nationalId; }
    public void setNationalId(String nationalId) { this.nationalId = nationalId; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getAddressLine1() { return addressLine1; }
    public void setAddressLine1(String a) { this.addressLine1 = a; }
    public String getPostcode() { return postcode; }
    public String getCountry() { return country; }
    public void setCountry(String country) { this.country = country; }

    public String maskedNationalId() {
        return nationalId == null || nationalId.length() < 4 ? "****" : "****" + nationalId.substring(nationalId.length() - 3);
    }
}
