import React, { useState, useEffect, useRef } from 'react';
import { Video, Circle, Maximize2, Minimize2, X } from 'lucide-react';
import { CrowdStatus } from '@/types/auth';
import ZoneBadge from './ZoneBadge';

interface LiveFeedCardProps {
  zone: string;
  /** Backend zone key for /video_feed/<zone> (Entrance, Queue, Sanctum, Exit) */
  feedZone?: string;
  isLive?: boolean;
  status?: CrowdStatus;
  lastUpdated?: Date;
}
// MJPEG streaming component that continuously refreshes
const MjpegFeed: React.FC<{ zone: string; fullscreen?: boolean }> = ({ zone, fullscreen }) => {
  const [error, setError] = useState(false);
  const [key, setKey] = useState(0);

  useEffect(() => {
    // Reconnect stream every 10 seconds if it gets stuck
    const interval = setInterval(() => {
      setKey(prev => prev + 1);
      setError(false);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className={`feed-placeholder w-full h-full flex flex-col items-center justify-center`}>
        <Video className="w-12 h-12 text-muted-foreground/50 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground/70">Feed unavailable</p>
        <button
          onClick={() => { setError(false); setKey(prev => prev + 1); }}
          className="mt-2 text-xs text-primary underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <img
      key={key}
      src={`http://localhost:5001/video_feed/${encodeURIComponent(zone)}`}
      alt={`${zone} live feed`}
      className="w-full h-full object-contain"
      onError={() => setError(true)}
    />
  );
};



// ↓ existing code continues below ↓


const LiveFeedCard: React.FC<LiveFeedCardProps> = ({ 
  zone, 
  feedZone,
  isLive = true, 
  status = 'normal',
  lastUpdated = new Date()
}) => {
  const apiZone = feedZone ?? zone;
  const [isFullscreen, setIsFullscreen] = useState(false);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const FeedContent = ({ fullscreen = false }: { fullscreen?: boolean }) => (
    <div className={`card-elevated overflow-hidden ${fullscreen ? 'w-full max-w-5xl' : ''} ${status === 'overcrowded' ? 'ring-2 ring-[hsl(var(--status-danger))] alert-glow' : ''}`}>
      {/* Feed Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-3">
          <Video className="w-4 h-4 text-muted-foreground" />
          <span className="font-medium text-sm">{zone}</span>
          <ZoneBadge status={status} />
        </div>
        <div className="flex items-center gap-3">
          {isLive && (
            <div className="flex items-center gap-1.5">
              <Circle className="w-2 h-2 fill-[hsl(var(--status-danger))] text-[hsl(var(--status-danger))] pulse-indicator" />
              <span className="text-xs font-medium text-[hsl(var(--status-danger))]">LIVE</span>
            </div>
          )}
          {fullscreen ? (
            <button
              onClick={() => setIsFullscreen(false)}
              className="p-1.5 rounded-md hover:bg-muted transition-colors"
              aria-label="Exit fullscreen"
            >
              <X className="w-4 h-4 text-muted-foreground" />
            </button>
          ) : (
            <button
              onClick={() => setIsFullscreen(true)}
              className="p-1.5 rounded-md hover:bg-muted transition-colors"
              aria-label="Enter fullscreen"
            >
              <Maximize2 className="w-4 h-4 text-muted-foreground" />
            </button>
          )}
        </div>
      </div>

      {/* Video Feed */}
      {/* Video Feed */}
      <div className={`${fullscreen ? 'aspect-video min-h-[60vh]' : 'aspect-video'} bg-black flex items-center justify-center overflow-hidden relative`}>
        <MjpegFeed
        zone={apiZone}
        fullscreen={fullscreen}
        />
      </div>

      {/* Footer with timestamp */}
      <div className="flex items-center justify-between px-4 py-2 bg-muted/30 border-t border-border">
        <span className="text-xs text-muted-foreground">Last frame: {formatTime(lastUpdated)}</span>
        <div className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-[hsl(var(--status-safe))]" />
          <span className="text-xs text-muted-foreground">Connected</span>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <FeedContent />
      
      {/* Fullscreen Overlay */}
      {isFullscreen && (
        <div className="fullscreen-overlay" onClick={() => setIsFullscreen(false)}>
          <div onClick={(e) => e.stopPropagation()}>
            <FeedContent fullscreen />
          </div>
        </div>
      )}
    </>
  );
};

export default LiveFeedCard;
