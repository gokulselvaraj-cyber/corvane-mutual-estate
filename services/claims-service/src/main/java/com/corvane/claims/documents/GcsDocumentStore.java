package com.corvane.claims.documents;

import com.google.cloud.storage.BlobId;
import com.google.cloud.storage.BlobInfo;
import com.google.cloud.storage.Storage;
import com.google.cloud.storage.StorageOptions;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Claim documents in GCS bucket corvane-claims-docs (europe-west2). The bucket is replicated by
 * infra/terraform to the DR bucket corvane-claims-docs-dr; claims does not write to the DR bucket itself.
 * Photos can show people, vehicles and addresses: personal data.
 */
@Component
public class GcsDocumentStore implements DocumentStore {

    private final Storage storage = StorageOptions.getDefaultInstance().getService();
    private final String bucket;

    public GcsDocumentStore(@Value("${corvane.documents.bucket:corvane-claims-docs}") String bucket) {
        this.bucket = bucket;
    }

    @Override
    public String put(String objectName, String contentType, byte[] bytes) {
        BlobInfo info = BlobInfo.newBuilder(BlobId.of(bucket, objectName)).setContentType(contentType).build();
        storage.create(info, bytes);
        return objectName;
    }

    @Override
    public byte[] get(String objectName) {
        return storage.readAllBytes(BlobId.of(bucket, objectName));
    }
}
