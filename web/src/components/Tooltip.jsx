import { h } from 'preact';
import { createPortal } from 'preact/compat';
import { useEffect, useRef, useState } from 'preact/hooks';

const TIP_SPACE = 20;

export default function Tooltip({ relativeTo, text }) {
  const [position, setPosition] = useState({ top: -Infinity, left: -Infinity });
  const portalRoot = document.getElementById('tooltips');
  const ref = useRef();

  useEffect(() => {
    if (ref && ref.current && relativeTo && relativeTo.current) {
      const windowWidth = window.innerWidth;
      const {
        x: relativeToX,
        y: relativeToY,
        width: relativeToWidth,
        height: relativeToHeight,
      } = relativeTo.current.getBoundingClientRect();
      const { width: tipWidth, height: tipHeight } = ref.current.getBoundingClientRect();

      const left = relativeToX + Math.round(relativeToWidth / 2) + window.scrollX;
      const top = relativeToY + Math.round(relativeToHeight / 2) + window.scrollY;

      let newTop = top - TIP_SPACE - tipHeight;
      let newLeft = left - Math.round(tipWidth / 2);
      // too far right
      if (newLeft + tipWidth + TIP_SPACE > windowWidth - window.scrollX) {
        newLeft = left - tipWidth - TIP_SPACE;
        newTop = top - Math.round(tipHeight / 2);
      }
      // too far left
      else if (newLeft < TIP_SPACE + window.scrollX) {
        newLeft = left + TIP_SPACE;
        newTop = top - Math.round(tipHeight / 2);
      }
      // too close to top
      else if (newTop <= TIP_SPACE + window.scrollY) {
        newTop = top + tipHeight + TIP_SPACE;
      }

      setPosition({ left: newLeft, top: newTop });
    }
  }, [relativeTo, ref]);

  const tooltip = (
    <div
      role="tooltip"
      className={`shadow max-w-lg absolute pointer-events-none bg-gray-900 dark:bg-gray-200 bg-opacity-80 rounded px-2 py-1 transition-opacity duration-200 opacity-0 text-gray-100 dark:text-gray-900 text-sm ${
        position.top >= 0 ? 'opacity-100' : ''
      }`}
      ref={ref}
      style={position.top >= 0 ? position : null}
    >
      {text}
    </div>
  );

  return portalRoot ? createPortal(tooltip, portalRoot) : tooltip;
}
