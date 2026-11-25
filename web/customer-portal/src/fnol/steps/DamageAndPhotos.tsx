import { uploadPhoto } from "../../api/claimsApi";
import { useToken } from "../../api/http";
import type { FnolState } from "../FnolWizard";

const MAX_PHOTOS = 8;
const MAX_BYTES = 10 * 1024 * 1024;

export function DamageAndPhotos({ state, update, next, back }: { state: FnolState; update: (p: Partial<FnolState>) => void; next: () => void; back: () => void }) {
  const token = useToken();
  async function add(files: FileList | null) {
    const ok = Array.from(files ?? []).filter((f) => f.size <= MAX_BYTES).slice(0, MAX_PHOTOS - state.photos.length);
    for (const f of ok) await uploadPhoto(token, state.draftId!, f);
    update({ photos: [...state.photos, ...ok] });
  }
  return (
    <section>
      <input type="file" accept="image/*" multiple onChange={(e) => add(e.target.files)} />
      <p>{state.photos.length} of {MAX_PHOTOS} photos added</p>
      <button onClick={back}>Back</button><button onClick={next}>Continue</button>
    </section>
  );
}
