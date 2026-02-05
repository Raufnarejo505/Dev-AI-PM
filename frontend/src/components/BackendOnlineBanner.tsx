import React, { useState, useEffect } from 'react';
import { useBackendStore } from '../store/backendStore';
import { useT } from '../i18n/I18nProvider';

export const BackendOnlineBanner: React.FC = () => {
  const status = useBackendStore((state) => state.status);
  const [show, setShow] = useState(false);
  const [wasOffline, setWasOffline] = useState(false);
  const t = useT();

  useEffect(() => {
    if (status === 'online' && wasOffline) {
      setShow(true);
      // Auto-dismiss after 5 seconds
      const timer = setTimeout(() => setShow(false), 5000);
      return () => clearTimeout(timer);
    }
    if (status === 'offline') {
      setWasOffline(true);
      setShow(false);
    }
  }, [status, wasOffline]);

  if (!show || status !== 'online') {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-green-600/90 backdrop-blur-sm border-b border-green-500/50 animate-slide-down">
      <div className="max-w-[1920px] mx-auto px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-200 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-green-50">
              {t('banners.backendOnlineLive')}
            </span>
          </div>
          <button
            onClick={() => setShow(false)}
            className="text-green-200 hover:text-green-100 text-xs"
          >
            X
          </button>
        </div>
      </div>
    </div>
  );
};

