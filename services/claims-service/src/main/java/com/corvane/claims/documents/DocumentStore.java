package com.corvane.claims.documents;

/** Where claim documents and damage photos are kept. */
public interface DocumentStore {
    /** Stores the bytes and returns the object name. */
    String put(String objectName, String contentType, byte[] bytes);
    byte[] get(String objectName);
}
