const size = 10000;
const payload = Array.from({ length: size }, (_, i) => ({
  status: i === size - 1 ? 'active' : 'canceled',
  current_period_end: '2025-01-01',
}));

const smallPayload = [{ status: 'active', current_period_end: '2025-01-01' }];

const largeJson = JSON.stringify(payload);
const smallJson = JSON.stringify(smallPayload);

console.time('Baseline (Parse + Find)');
for(let i=0; i<1000; i++) {
  const parsed = JSON.parse(largeJson);
  const found = parsed.find(item => item.status === 'active');
}
console.timeEnd('Baseline (Parse + Find)');

console.time('Optimized (Parse + Index)');
for(let i=0; i<1000; i++) {
  const parsed = JSON.parse(smallJson);
  const found = parsed.length > 0 ? parsed[0] : undefined;
}
console.timeEnd('Optimized (Parse + Index)');
