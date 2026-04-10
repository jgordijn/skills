export const TOOL_NAME = 'get_current_pi_session_settings';
export const TOOL_DESCRIPTION =
  'Get the active pi provider/model route and thinking level for delegate launches.';

export function buildCurrentPiSessionSettings(model, thinkingLevel) {
  if (!model?.provider || !model?.id) {
    throw new Error('No current pi model is selected.');
  }

  const normalizedThinking = String(thinkingLevel ?? '').trim() || 'off';
  const routedModel = `${model.provider}/${model.id}`;
  const text = [
    'Current pi session settings:',
    `- provider: ${model.provider}`,
    `- model: ${routedModel}`,
    `- thinking: ${normalizedThinking}`,
  ].join('\n');

  return {
    provider: model.provider,
    modelId: model.id,
    model: routedModel,
    thinking: normalizedThinking,
    text,
  };
}

export function registerCurrentPiSessionSettingsTool(pi, { Type, getThinkingLevel }) {
  const tool = {
    name: TOOL_NAME,
    label: 'Current Pi Session Settings',
    description: TOOL_DESCRIPTION,
    parameters: Type.Object({}),
    async execute(_toolCallId, _params, _signal, _onUpdate, ctx) {
      const settings = buildCurrentPiSessionSettings(ctx.model, getThinkingLevel());
      return {
        content: [{ type: 'text', text: settings.text }],
        details: settings,
      };
    },
  };

  pi.registerTool(tool);
  return tool;
}

export async function activate(pi, dependencies) {
  const resolvedDependencies = dependencies ?? (await import('@mariozechner/pi-ai'));
  return registerCurrentPiSessionSettingsTool(pi, {
    Type: resolvedDependencies.Type,
    getThinkingLevel: () => pi.getThinkingLevel(),
  });
}

export default activate;