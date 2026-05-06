// Driver: read spec JSON from argv[2], emit N variants per problem as JSON.
import { generateVariant, mulberry32 } from './engine.js';
import { readFileSync } from 'node:fs';

const [, , specPath, nStr] = process.argv;
const n = parseInt(nStr, 10);
const spec = JSON.parse(readFileSync(specPath, 'utf-8'));
const out = { samples: [] };
for (const prob of spec.problems || []) {
  const rng = mulberry32(parseInt(prob.id.replace(/\D/g, '') || '1', 10));
  const variants = [];
  let failures = 0;
  for (let i = 0; i < n; i++) {
    try {
      variants.push(generateVariant(prob, rng));
    } catch (e) {
      failures++;
      variants.push({ error: e.message });
    }
  }
  out.samples.push({ id: prob.id, variants, failures });
}
console.log(JSON.stringify(out));
