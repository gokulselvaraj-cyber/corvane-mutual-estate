import { Link } from "react-router-dom";
import { LINES } from "../quote/lines";

export function Home() {
  return (
    <main>
      <h1>Corvane Mutual</h1>
      <ul>{LINES.map((l) => <li key={l.code}><Link to={`/quote/${l.code}`}>{l.name} insurance</Link></li>)}</ul>
      <Link to="/claims/new">Report a claim</Link>
    </main>
  );
}
