import { h } from 'preact';
import { memo } from 'preact/compat';

export function StarRecording({ className = '' }) {
  return (
    <svg className={`fill-current ${className}`} viewBox="0 0 24 24">
      <path d="M14 2H6a2 2 0 00-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6m.5 16.9L12 17.5 9.5 19l.7-2.8L8 14.3l2.9-.2 1.1-2.7 1.1 2.6 2.9.2-2.2 1.9.7 2.8M13 9V3.5L18.5 9H13z" />
    </svg>
  );
}

export default memo(StarRecording);
