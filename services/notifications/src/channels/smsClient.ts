import { request } from "undici";

export class SmsClient {
  constructor(private url: string, private apiKey: string) {}

  async send(to: string, text: string): Promise<void> {
    const res = await request(this.url, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${this.apiKey}` },
      body: JSON.stringify({ to, text, sender: "CORVANE" }),
      headersTimeout: 3000,
    });
    if (res.statusCode >= 300) throw new Error(`sms failed: ${res.statusCode}`);
  }
}
