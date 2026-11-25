package com.corvane.policy.service;

import com.corvane.policy.domain.RatingInput;
import com.ibm.ctg.client.ECIRequest;
import com.ibm.ctg.client.JavaGateway;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.charset.Charset;

/**
 * Calls the mainframe rating engine: CICS program PRMCALC0 on CTG server CORVCTG1, COMMAREA layout PRMCOMM.
 * The COMMAREA is EBCDIC (cp037); amounts come back as zoned decimal with two implied decimals.
 */
@Component
public class MainframePremiumAdapter implements PremiumEngine {

    static final int COMMAREA_LENGTH = 200;
    private static final Charset EBCDIC = Charset.forName("Cp037");

    private final String host;
    private final int port;
    private final String server;
    private final String program;
    private final int timeoutMs;

    public MainframePremiumAdapter(@Value("${ctg.host}") String host, @Value("${ctg.port}") int port,
                                   @Value("${ctg.server}") String server, @Value("${ctg.program}") String program,
                                   @Value("${ctg.timeout-ms}") int timeoutMs) {
        this.host = host;
        this.port = port;
        this.server = server;
        this.program = program;
        this.timeoutMs = timeoutMs;
    }

    @Override
    public String name() { return "mainframe"; }

    @Override
    @CircuitBreaker(name = "ctg")
    public Priced price(RatingInput input) {
        byte[] commarea = toCommarea(input);
        try {
            JavaGateway gateway = new JavaGateway(host, port);
            try {
                ECIRequest req = new ECIRequest(ECIRequest.ECI_SYNC, server, null, null, program, null,
                        commarea, COMMAREA_LENGTH, ECIRequest.ECI_NO_EXTEND, 0);
                req.setECITimeout((short) (timeoutMs / 1000));
                gateway.flow(req);
                if (req.getCicsRc() != 0) {
                    throw new MainframeRatingException("PRMCALC0 returned CICS rc " + req.getCicsRc());
                }
                return fromCommarea(req.Commarea);
            } finally {
                gateway.close();
            }
        } catch (IOException e) {
            throw new MainframeRatingException("CTG " + server + " unreachable: " + e.getMessage());
        }
    }

    /** PRMCOMM: LINE-CODE X(3), POSTCODE X(8), HOLDER-AGE 9(3), SUM-INSURED 9(9)V99, VOL-EXCESS 9(5)V99, PRIOR-CLAIMS 9(2). */
    byte[] toCommarea(RatingInput in) {
        String s = String.format("%-3s%-8s%03d%011d%07d%02d", in.line().name(), in.postcode(), in.holderAge(),
                in.sumInsured().movePointRight(2).longValue(), in.voluntaryExcess().movePointRight(2).longValue(),
                Math.min(in.priorClaims(), 99));
        byte[] out = new byte[COMMAREA_LENGTH];
        byte[] b = s.getBytes(EBCDIC);
        System.arraycopy(b, 0, out, 0, b.length);
        return out;
    }

    /** Response area starts at offset 100: BASE-PREMIUM 9(9)V99, REFER-FLAG X, REFER-REASON X(60). */
    Priced fromCommarea(byte[] area) {
        String s = new String(area, EBCDIC);
        BigDecimal premium = new BigDecimal(s.substring(100, 111)).movePointLeft(2);
        String refer = s.charAt(111) == 'Y' ? s.substring(112, 172).trim() : null;
        return new Priced(premium, refer);
    }

    public static class MainframeRatingException extends RuntimeException {
        public MainframeRatingException(String m) { super(m); }
    }
}
