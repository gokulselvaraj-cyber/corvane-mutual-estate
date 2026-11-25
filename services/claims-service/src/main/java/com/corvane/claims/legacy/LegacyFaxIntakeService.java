package com.corvane.claims.legacy;

import com.corvane.claims.api.ClaimDtos.FnolRequest;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * Parsed OCR'd fax claim forms (form CF-7) into FNOL requests. The fax line was switched off in 2024.
 * Not a Spring bean and not referenced anywhere; kept "in case brokers ask".
 */
public class LegacyFaxIntakeService {

    public FnolRequest parse(String ocrText) {
        String[] lines = ocrText.split("\\R");
        String policy = value(lines, "POLICY NO:");
        LocalDate date = LocalDate.parse(value(lines, "DATE OF LOSS:"));
        String cause = value(lines, "CAUSE:");
        BigDecimal amount = new BigDecimal(value(lines, "AMOUNT:").replace(",", ""));
        return new FnolRequest(policy, date, cause, value(lines, "DETAILS:"), null, amount, null, null, null);
    }

    private static String value(String[] lines, String label) {
        for (String l : lines) {
            if (l.startsWith(label)) {
                return l.substring(label.length()).trim();
            }
        }
        throw new IllegalArgumentException("Missing " + label);
    }
}
