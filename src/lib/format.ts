export const formatDate = (d: Date) =>
  d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });

export const kindLabel = (kind?: string | null) =>
  kind === 'tips' ? 'Tricks & Tips Thursday' : kind === 'radar' ? 'AI Radar' : '';
