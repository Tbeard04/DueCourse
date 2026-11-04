import digestJson from "@/data/digest.json";
import {
  daysPhrase,
  formatDueDate,
  type Digest,
  type DigestSection,
} from "@/lib/digest";

const digest = digestJson as Digest;

function DeadlineTable({ section }: { section: DigestSection }) {
  return (
    <div className="table-wrap">
      <table>
        <caption>{section.label}</caption>
        <thead>
          <tr>
            <th scope="col">Company</th>
            <th scope="col">Filing</th>
            <th scope="col">Due date</th>
            <th scope="col" className="num">
              Due in
            </th>
          </tr>
        </thead>
        <tbody>
          {section.items.map((item) => (
            <tr key={`${item.companyNumber}-${item.filing}`}>
              <th scope="row">
                {item.companyName}
                <span className="co-no">{item.companyNumber}</span>
              </th>
              <td>{item.filing}</td>
              <td className="due">{formatDueDate(item.dueDate)}</td>
              <td className="num">{daysPhrase(item.daysUntilDue)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Page() {
  const actionable = digest.sections.filter(
    (s) => s.slug !== "ok" && s.items.length > 0,
  );
  const onTrack = digest.sections.find((s) => s.slug === "ok");

  return (
    <main>
      <header>
        <h1>Weekly filing digest</h1>
        <p className="lede">
          A demo accountancy portfolio of {digest.portfolioSize} real UK
          companies, triaged against the live Companies House register.
        </p>
        <p className="meta">
          Snapshot as of {digest.asOf} · regenerates every Monday
        </p>
      </header>

      <ul className="tiles">
        {digest.sections.map((s) => (
          <li key={s.slug} className={`t-${s.slug}`}>
            <b>{s.items.length}</b>
            <span>{s.label}</span>
          </li>
        ))}
      </ul>

      {actionable.map((section) => (
        <section key={section.slug}>
          <h2>
            <span className={`tag tag-${section.slug}`}>{section.label}</span>
            <span className="count">
              {section.items.length} deadline
              {section.items.length !== 1 ? "s" : ""}
            </span>
          </h2>
          <DeadlineTable section={section} />
        </section>
      ))}

      {onTrack && onTrack.items.length > 0 && (
        <section>
          {/* The long tail: collapsed so the page leads with what needs action. */}
          <details>
            <summary>
              {onTrack.label}{" "}
              <span className="count">({onTrack.items.length} deadlines)</span>
            </summary>
            <DeadlineTable section={onTrack} />
          </details>
        </section>
      )}

      <footer>
        <p>
          Rebuilt every Monday by a scheduled GitHub Action — no servers and no
          manual steps. Deadlines and urgency are computed deterministically
          from{" "}
          <a href="https://developer.company-information.service.gov.uk/">
            Companies House public data
          </a>
          ; no AI touches this page.
        </p>
        <p>
          The human-in-the-loop drafting and review queue run privately inside
          the practice — see the{" "}
          <a href="https://github.com/Tbeard04/DueCourse">
            source and engagement pack
          </a>
          . Nothing is ever sent automatically. Generated {digest.generated}.
        </p>
      </footer>
    </main>
  );
}
