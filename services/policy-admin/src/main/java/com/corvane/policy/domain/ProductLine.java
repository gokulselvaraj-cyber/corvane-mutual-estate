package com.corvane.policy.domain;

/** The twelve Corvane product lines. The three-letter code is shared with the mainframe (POLREC LINE-CODE). */
public enum ProductLine {
    MTR("Motor"), HOM("Home buildings"), CNT("Home contents"), TRV("Travel"), PET("Pet"), LLD("Landlord"),
    MAR("Marine cargo"), CPR("Commercial property"), PLB("Public liability"), PIN("Professional indemnity"),
    CYB("Cyber"), GDG("Gadget");

    private final String label;

    ProductLine(String label) { this.label = label; }

    public String label() { return label; }
}
