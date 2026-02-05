import React from 'react';
import { useBackendStore } from '../store/backendStore';
import { useT } from '../i18n/I18nProvider';

export const BackendStatusBanner: React.FC = () => {
  const status = useBackendStore((state) => state.status);
  const lastCheck = useBackendStore((state) => state.lastCheck);
  const t = useT();
  
  if (status === 'online' || status === 'checking') {
    return null;
  }
  
  const formatTime = (date: Date | null) => {
    if (!date) return t('time.never');
    const secondsAgo = Math.floor((Date.now() - date.getTime()) / 1000);
    if (secondsAgo < 60) return `${secondsAgo}${t('time.secondsAgo')}`;
    const minutesAgo = Math.floor(secondsAgo / 60);
    return `${minutesAgo}${t('time.minutesAgo')}`;
  };
  
  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-amber-600/90 backdrop-blur-sm border-b border-amber-500/50">
      <div className="max-w-7xl mx-auto px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-amber-200 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-amber-50">
              {t('banners.backendOfflineFallback')}
            </span>
            {lastCheck && (
              <span className="text-xs text-amber-200/80">
                ({t('time.lastCheck')}: {formatTime(lastCheck)})
              </span>
            )}
          </div>
          <div className="text-xs text-amber-200/80">
            {t('banners.autoRecoveryEnabled')}
          </div>
        </div>
      </div>
    </div>
  );
};

