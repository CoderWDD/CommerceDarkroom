"use client";

import React from 'react';
import { useStudioStore } from '@/stores/useStudioStore';
import { ScriptCardItem } from './ScriptCardItem';

export const PerspectiveScriptGrid: React.FC = () => {
  const { currentSession } = useStudioStore();
  const perspectives = currentSession?.perspectives || [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {perspectives.map((perspective, index) => (
        <ScriptCardItem
          key={perspective.id}
          perspective={perspective}
          index={index}
        />
      ))}
    </div>
  );
};
