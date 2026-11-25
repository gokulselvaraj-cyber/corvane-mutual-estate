import { useParams } from "react-router-dom";
import { useState } from "react";
import { requestQuote, bindQuote, type QuoteResponse } from "../api/policyApi";
import { useToken } from "../api/http";
import { FORMS } from "../quote/forms";
import type { LineCode } from "../model/Policy";

/** Journey J4 starts here: quote, then bind. */
export function QuotePage() {
  const { line } = useParams<{ line: LineCode }>();
  const token = useToken();
  const [quote, setQuote] = useState<QuoteResponse>();
  const Form = FORMS[line!];
  if (!Form) return <p>Unknown product.</p>;
  return (
    <main>
      <Form onSubmit={async (req) => setQuote(await requestQuote(token, req))} />
      {quote && (
        <aside>
          <p>Annual premium {quote.currency} {quote.annualPremium.toFixed(2)} (includes IPT {quote.ipt.toFixed(2)})</p>
          {quote.referred ? <p>We need to check a few details before we can offer cover.</p>
            : <button onClick={() => bindQuote(token, quote.quoteId)}>Buy this policy</button>}
        </aside>
      )}
    </main>
  );
}
