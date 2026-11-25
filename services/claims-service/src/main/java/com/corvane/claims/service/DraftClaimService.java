package com.corvane.claims.service;

import com.corvane.claims.api.ClaimDtos.DraftRequest;
import com.corvane.claims.api.ClaimDtos.DraftResponse;
import com.corvane.claims.api.ClaimDtos.PhotoResponse;
import com.corvane.claims.documents.DocumentStore;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.OffsetDateTime;
import java.util.UUID;

/** Drafts back the portal FNOL wizard step DamageAndPhotos. Drafts expire after 72 hours. */
@Service
public class DraftClaimService {

    private static final long MAX_PHOTO_BYTES = 15L * 1024 * 1024;
    private final DocumentStore documents;

    public DraftClaimService(DocumentStore documents) {
        this.documents = documents;
    }

    public DraftResponse start(DraftRequest request, String userId) {
        return new DraftResponse(UUID.randomUUID(), OffsetDateTime.now().plusHours(72));
    }

    public PhotoResponse attachPhoto(UUID draftId, MultipartFile file) {
        if (file.getSize() > MAX_PHOTO_BYTES) {
            throw new IllegalArgumentException("Photo larger than 15 MB");
        }
        try {
            String name = documents.put("drafts/" + draftId + "/" + UUID.randomUUID() + ".jpg",
                    file.getContentType(), file.getBytes());
            return new PhotoResponse(draftId, name, file.getSize());
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
