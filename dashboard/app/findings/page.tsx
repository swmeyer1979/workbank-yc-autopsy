import { readFileSync } from "fs";
import { join } from "path";
import { remark } from "remark";
import remarkHtml from "remark-html";

async function getFindings(): Promise<string> {
  // In static export, we read the file at build time
  const mdPath = join(process.cwd(), "findings.md");
  const content = readFileSync(mdPath, "utf-8");
  const result = await remark().use(remarkHtml, { sanitize: false }).process(content);
  return result.toString();
}

export default async function FindingsPage() {
  const html = await getFindings();

  return (
    <div className="container">
      <div className="findings-page">
        <div className="findings-back">
          <a href="/">← Back to dashboard</a>
        </div>
        <div dangerouslySetInnerHTML={{ __html: html }} />
      </div>
    </div>
  );
}
