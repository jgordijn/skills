import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import activate, {
  TOOL_NAME,
  TOOL_DESCRIPTION,
  buildCurrentPiSessionSettings,
  registerCurrentPiSessionSettingsTool,
} from '../extensions/current-pi-session-settings.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

test('buildCurrentPiSessionSettings returns routed model and thinking', () => {
  const settings = buildCurrentPiSessionSettings(
    { provider: 'github-copilot', id: 'gpt-5.4' },
    'high',
  );

  assert.deepEqual(settings, {
    provider: 'github-copilot',
    modelId: 'gpt-5.4',
    model: 'github-copilot/gpt-5.4',
    thinking: 'high',
    text: [
      'Current pi session settings:',
      '- provider: github-copilot',
      '- model: github-copilot/gpt-5.4',
      '- thinking: high',
    ].join('\n'),
  });
});

test('buildCurrentPiSessionSettings normalizes missing thinking to off', () => {
  const withBlankThinking = buildCurrentPiSessionSettings(
    { provider: 'openai', id: 'gpt-5.4-mini' },
    '',
  );
  const withUndefinedThinking = buildCurrentPiSessionSettings(
    { provider: 'openai', id: 'gpt-5.4-mini' },
    undefined,
  );

  assert.equal(withBlankThinking.thinking, 'off');
  assert.match(withBlankThinking.text, /- thinking: off$/);
  assert.equal(withUndefinedThinking.thinking, 'off');
  assert.match(withUndefinedThinking.text, /- thinking: off$/);
});

test('buildCurrentPiSessionSettings rejects missing model data', () => {
  assert.throws(() => buildCurrentPiSessionSettings(undefined, 'high'), /No current pi model/);
  assert.throws(
    () => buildCurrentPiSessionSettings({ provider: 'openai' }, 'high'),
    /No current pi model/,
  );
  assert.throws(
    () => buildCurrentPiSessionSettings({ id: 'gpt-5.4' }, 'high'),
    /No current pi model/,
  );
});

test('registerCurrentPiSessionSettingsTool registers an executable tool', async () => {
  const registrations = [];
  const pi = {
    registerTool(tool) {
      registrations.push(tool);
    },
  };
  const typeCalls = [];
  const Type = {
    Object(shape) {
      typeCalls.push(shape);
      return { type: 'object', shape };
    },
  };

  const tool = registerCurrentPiSessionSettingsTool(pi, {
    Type,
    getThinkingLevel: () => 'medium',
  });

  assert.equal(registrations.length, 1);
  assert.equal(registrations[0], tool);
  assert.equal(tool.name, TOOL_NAME);
  assert.equal(tool.description, TOOL_DESCRIPTION);
  assert.deepEqual(typeCalls, [{}]);

  const result = await tool.execute('tool-call-id', {}, undefined, undefined, {
    model: { provider: 'anthropic', id: 'claude-sonnet-4-6' },
  });

  assert.deepEqual(result, {
    content: [
      {
        type: 'text',
        text: [
          'Current pi session settings:',
          '- provider: anthropic',
          '- model: anthropic/claude-sonnet-4-6',
          '- thinking: medium',
        ].join('\n'),
      },
    ],
    details: {
      provider: 'anthropic',
      modelId: 'claude-sonnet-4-6',
      model: 'anthropic/claude-sonnet-4-6',
      thinking: 'medium',
      text: [
        'Current pi session settings:',
        '- provider: anthropic',
        '- model: anthropic/claude-sonnet-4-6',
        '- thinking: medium',
      ].join('\n'),
    },
  });
});

test('activate wires pi.getThinkingLevel into the registered tool', async () => {
  const registrations = [];
  const pi = {
    getThinkingLevel() {
      return 'xhigh';
    },
    registerTool(tool) {
      registrations.push(tool);
    },
  };
  const deps = {
    Type: {
      Object(shape) {
        return { type: 'object', shape };
      },
    },
  };

  const tool = await activate(pi, deps);

  assert.equal(registrations.length, 1);
  assert.equal(registrations[0], tool);

  const result = await tool.execute('tool-call-id', {}, undefined, undefined, {
    model: { provider: 'openrouter', id: 'anthropic/claude-sonnet-4-6' },
  });

  assert.equal(result.details.model, 'openrouter/anthropic/claude-sonnet-4-6');
  assert.equal(result.details.thinking, 'xhigh');
});

test('activate loads dependencies when they are not provided', async () => {
  const registrations = [];
  const pi = {
    getThinkingLevel() {
      return 'low';
    },
    registerTool(tool) {
      registrations.push(tool);
    },
  };
  const moduleDir = path.join(repoRoot, 'node_modules', '@mariozechner', 'pi-ai');
  await fs.mkdir(moduleDir, { recursive: true });
  await fs.writeFile(
    path.join(moduleDir, 'package.json'),
    JSON.stringify({
      name: '@mariozechner/pi-ai',
      type: 'module',
      main: './index.js',
      exports: './index.js',
    }),
    'utf-8',
  );
  await fs.writeFile(
    path.join(moduleDir, 'index.js'),
    "export const Type = { Object(shape) { return { type: 'object', shape }; } };\n",
    'utf-8',
  );

  try {
    const tool = await activate(pi);
    assert.equal(registrations[0], tool);

    const result = await tool.execute('tool-call-id', {}, undefined, undefined, {
      model: { provider: 'github-copilot', id: 'gpt-5.4-mini' },
    });

    assert.equal(result.details.model, 'github-copilot/gpt-5.4-mini');
    assert.equal(result.details.thinking, 'low');
  } finally {
    await fs.rm(path.join(repoRoot, 'node_modules'), { recursive: true, force: true });
  }
});
