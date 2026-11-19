import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import test from "node:test";
import ts from "typescript";

const source = readFileSync(new URL("../src/lib/api.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const { loadDashboard } = await import("data:text/javascript;base64," + Buffer.from(compiled).toString("base64"));
const fixture = JSON.parse(readFileSync(new URL("../src/mocks/dashboard.json", import.meta.url), "utf8"));

function readyResponses() {
  return structuredClone({
    "dataset-summary": fixture.ready.dataset_summary,
    predictions: fixture.ready.predictions,
    "model-info": fixture.ready.model_info,
    evaluations: fixture.ready.evaluations,
  });
}

function mockApi(context, responses) {
  return context.mock.method(globalThis, "fetch", async url => {
    const endpoint = String(url).split("/").at(-1);
    assert.ok(endpoint in responses, "Unexpected endpoint " + endpoint);
    return new Response(JSON.stringify(responses[endpoint]), { status: 200 });
  });
}

test("returns one coherent snapshot with evaluations", async context => {
  const fetch = mockApi(context, readyResponses());
  const result = await loadDashboard();
  assert.equal(result.status, "ready");
  assert.equal(result.snapshot.summary.data.processed_rows, 2);
  assert.equal(result.snapshot.evaluations.status, "ready");
  assert.equal(fetch.mock.callCount(), 4);
});

test("preparing stops before accessing null result data", async context => {
  const fetch = mockApi(context, { "dataset-summary": fixture.preparing.dataset_summary });
  const result = await loadDashboard();
  assert.equal(result.status, "preparing");
  assert.equal(fetch.mock.callCount(), 1);
  assert.equal("snapshot" in result, false);
});

test("shows structured backend errors", async context => {
  mockApi(context, { "dataset-summary": fixture.failed.dataset_summary });
  const result = await loadDashboard();
  assert.equal(result.status, "failed");
  assert.equal(result.message, fixture.failed.dataset_summary.error.message);
});

test("withholds responses from different dataset versions", async context => {
  const responses = readyResponses();
  responses.predictions.dataset_version = "changed-dataset";
  mockApi(context, responses);
  assert.equal((await loadDashboard()).status, "preparing");
});

test("withholds responses from different model versions", async context => {
  const responses = readyResponses();
  responses.evaluations.model_version = "changed-model";
  mockApi(context, responses);
  assert.equal((await loadDashboard()).status, "preparing");
});

test("an absent legacy evaluation remains visible as its own status", async context => {
  const responses = readyResponses();
  responses.evaluations = {
    ...responses.evaluations, status: "failed", data: null,
    error: { code: "EVALUATIONS_NOT_AVAILABLE", message: "Evaluasi belum tersedia." },
  };
  mockApi(context, responses);
  const result = await loadDashboard();
  assert.equal(result.status, "ready");
  assert.equal(result.snapshot.evaluations.status, "failed");
});

test("accepts empty predictions and absent historical labels", async context => {
  const responses = readyResponses();
  responses.predictions.data = { processed_rows: 0, predictions: [], warnings: [] };
  responses["dataset-summary"].data.actual_churn = null;
  mockApi(context, responses);
  const result = await loadDashboard();
  assert.equal(result.status, "ready");
  assert.equal(result.snapshot.predictions.data.predictions.length, 0);
});

test("reports network failures with a readable message", async context => {
  context.mock.method(globalThis, "fetch", async () => { throw new TypeError("fetch failed"); });
  await assert.rejects(loadDashboard(), /Backend tidak dapat dihubungi/);
});
