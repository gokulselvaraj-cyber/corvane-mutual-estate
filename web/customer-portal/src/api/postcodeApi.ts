/** External postcode lookup (outside the Corvane boundary). Called straight from the browser. */
const POSTCODE_API = "https://postcode.lookup.example/v1";

export interface PostcodeHit { postcode: string; town: string; lines: string[] }

export async function lookupPostcode(postcode: string): Promise<PostcodeHit[]> {
  const res = await fetch(`${POSTCODE_API}/addresses?postcode=${encodeURIComponent(postcode.trim())}`);
  if (!res.ok) return [];
  return (await res.json()).results as PostcodeHit[];
}
