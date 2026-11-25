package com.sentinelexchange.sdk;

import jakarta.xml.bind.JAXB;
import java.io.StringReader;
import java.io.StringWriter;

final class XmlCodec {
    private XmlCodec() { }

    static String envelope(String operation, Object body) {
        StringWriter w = new StringWriter();
        JAXB.marshal(body, w);
        return "<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\"><soap:Body><" + operation
                + " xmlns=\"urn:sentinel:claims:v2\">" + w + "</" + operation + "></soap:Body></soap:Envelope>";
    }

    static <T> T decode(String xml, Class<T> type) {
        return type == Void.class ? null : JAXB.unmarshal(new StringReader(xml), type);
    }
}
