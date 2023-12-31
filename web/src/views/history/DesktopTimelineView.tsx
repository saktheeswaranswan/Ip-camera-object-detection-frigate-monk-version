import { useApiHost } from "@/api";
import TimelineEventOverlay from "@/components/overlay/TimelineDataOverlay";
import VideoPlayer from "@/components/player/VideoPlayer";
import ActivityScrubber from "@/components/scrubber/ActivityScrubber";
import ActivityIndicator from "@/components/ui/activity-indicator";
import { FrigateConfig } from "@/types/frigateConfig";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import useSWR from "swr";
import Player from "video.js/dist/types/player";
import TimelineItemCard from "@/components/card/TimelineItemCard";
import { getTimelineHoursForDay } from "@/utils/historyUtil";

type DesktopTimelineViewProps = {
  timelineData: CardsData;
  allPreviews: Preview[];
  initialPlayback: TimelinePlayback;
};

export default function DesktopTimelineView({
  timelineData,
  allPreviews,
  initialPlayback,
}: DesktopTimelineViewProps) {
  const apiHost = useApiHost();
  const { data: config } = useSWR<FrigateConfig>("config");
  const timezone = useMemo(
    () =>
      config?.ui?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
    [config]
  );

  const [selectedPlayback, setSelectedPlayback] = useState(initialPlayback);

  const playerRef = useRef<Player | undefined>(undefined);
  const previewRef = useRef<Player | undefined>(undefined);

  const [scrubbing, setScrubbing] = useState(false);
  const [focusedItem, setFocusedItem] = useState<Timeline | undefined>(
    undefined
  );

  const [seeking, setSeeking] = useState(false);
  const [timeToSeek, setTimeToSeek] = useState<number | undefined>(undefined);

  const annotationOffset = useMemo(() => {
    if (!config) {
      return 0;
    }

    return (
      (config.cameras[initialPlayback.camera]?.detect?.annotation_offset || 0) /
      1000
    );
  }, [config]);

  const timelineTime = useMemo(() => {
    if (!selectedPlayback || selectedPlayback.timelineItems.length == 0) {
      return selectedPlayback.range.start;
    }

    return selectedPlayback.timelineItems.at(0)!!.timestamp;
  }, [selectedPlayback]);

  const recordingParams = useMemo(() => {
    return {
      before: selectedPlayback.range.end,
      after: selectedPlayback.range.start,
    };
  }, [selectedPlayback]);
  const { data: recordings } = useSWR<Recording[]>(
    selectedPlayback
      ? [`${selectedPlayback.camera}/recordings`, recordingParams]
      : null,
    { revalidateOnFocus: false }
  );

  const playbackUri = useMemo(() => {
    if (!selectedPlayback) {
      return "";
    }

    const date = new Date(selectedPlayback.range.start * 1000);
    return `${apiHost}vod/${date.getFullYear()}-${
      date.getMonth() + 1
    }/${date.getDate()}/${date.getHours()}/${
      selectedPlayback.camera
    }/${timezone.replaceAll("/", ",")}/master.m3u8`;
  }, [selectedPlayback]);

  const onSelectItem = useCallback(
    (timeline: Timeline | undefined) => {
      if (timeline) {
        setFocusedItem(timeline);
        const selected = timeline.timestamp;
        playerRef.current?.pause();

        let seekSeconds = 0;
        (recordings || []).every((segment) => {
          // if the next segment is past the desired time, stop calculating
          if (segment.start_time > selected) {
            return false;
          }

          if (segment.end_time < selected) {
            seekSeconds += segment.end_time - segment.start_time;
            return true;
          }

          seekSeconds +=
            segment.end_time -
            segment.start_time -
            (segment.end_time - selected);
          return true;
        });
        playerRef.current?.currentTime(seekSeconds);
      } else {
        setFocusedItem(undefined);
      }
    },
    [annotationOffset, recordings, playerRef]
  );

  const onScrubTime = useCallback(
    (data: { time: Date }) => {
      if (!selectedPlayback.relevantPreview) {
        return;
      }

      if (playerRef.current?.paused() == false) {
        setScrubbing(true);
        playerRef.current?.pause();
      }

      const seekTimestamp = data.time.getTime() / 1000;
      const seekTime = seekTimestamp - selectedPlayback.relevantPreview.start;
      setTimeToSeek(Math.round(seekTime));
    },
    [scrubbing, playerRef, selectedPlayback]
  );

  const onStopScrubbing = useCallback(
    (data: { time: Date }) => {
      const playbackTime = data.time.getTime() / 1000;
      playerRef.current?.currentTime(
        playbackTime - selectedPlayback.range.start
      );
      setScrubbing(false);
      playerRef.current?.play();
    },
    [selectedPlayback, playerRef]
  );

  // handle seeking to next frame when seek is finished
  useEffect(() => {
    if (seeking) {
      return;
    }

    if (timeToSeek && timeToSeek != previewRef.current?.currentTime()) {
      setSeeking(true);
      previewRef.current?.currentTime(timeToSeek);
    }
  }, [timeToSeek, seeking]);

  // handle loading main playback when selected hour changes
  useEffect(() => {
    if (!playerRef.current) {
      return;
    }

    playerRef.current.src({
      src: playbackUri,
      type: "application/vnd.apple.mpegurl",
    });
  }, [playerRef, selectedPlayback]);

  const timelineStack = useMemo(
    () =>
      getTimelineHoursForDay(
        selectedPlayback.camera,
        timelineData,
        allPreviews,
        timelineTime
      ),
    []
  );

  if (!config) {
    return <ActivityIndicator />;
  }

  return (
    <div className="w-full">
      <div className="flex">
        <>
          <div className="w-2/3 bg-black flex justify-center items-center">
            <div
              className={`w-full relative ${
                selectedPlayback.relevantPreview != undefined && scrubbing
                  ? "hidden"
                  : "visible"
              }`}
            >
              <VideoPlayer
                options={{
                  preload: "auto",
                  autoplay: true,
                  sources: [
                    {
                      src: playbackUri,
                      type: "application/vnd.apple.mpegurl",
                    },
                  ],
                }}
                seekOptions={{ forward: 10, backward: 5 }}
                onReady={(player) => {
                  playerRef.current = player;
                  player.currentTime(
                    timelineTime - selectedPlayback.range.start
                  );
                  player.on("playing", () => {
                    onSelectItem(undefined);
                  });
                }}
                onDispose={() => {
                  playerRef.current = undefined;
                }}
              >
                {focusedItem && (
                  <TimelineEventOverlay
                    timeline={focusedItem}
                    cameraConfig={config.cameras[selectedPlayback.camera]}
                  />
                )}
              </VideoPlayer>
            </div>
            {selectedPlayback.relevantPreview && (
              <div className={`w-full ${scrubbing ? "visible" : "hidden"}`}>
                <VideoPlayer
                  options={{
                    preload: "auto",
                    autoplay: false,
                    controls: false,
                    muted: true,
                    loadingSpinner: false,
                    sources: [
                      {
                        src: `${selectedPlayback.relevantPreview?.src}`,
                        type: "video/mp4",
                      },
                    ],
                  }}
                  seekOptions={{}}
                  onReady={(player) => {
                    previewRef.current = player;
                    player.on("seeked", () => setSeeking(false));
                  }}
                  onDispose={() => {
                    previewRef.current = undefined;
                  }}
                />
              </div>
            )}
          </div>
        </>
        <div className="px-2 h-[608px] overflow-auto">
          {selectedPlayback.timelineItems.map((timeline) => {
            return (
              <TimelineItemCard
                key={timeline.timestamp}
                timeline={timeline}
                relevantPreview={selectedPlayback.relevantPreview}
                onSelect={() => onSelectItem(timeline)}
              />
            );
          })}
        </div>
      </div>
      <div className="m-1 max-h-72 2xl:max-h-80 3xl:max-h-96 overflow-auto">
        {timelineStack.map((timeline) => {
          const isSelected =
            timeline.range.start == selectedPlayback.range.start;

          return (
            <div
              key={timeline.range.start}
              className={`${isSelected ? "border border-primary" : ""}`}
            >
              <ActivityScrubber
                items={[]}
                timeBars={
                  isSelected && selectedPlayback.relevantPreview
                    ? [{ time: new Date(timelineTime * 1000), id: "playback" }]
                    : []
                }
                options={{
                  snap: null,
                  min: new Date(timeline.range.start * 1000),
                  max: new Date(timeline.range.end * 1000),
                  zoomable: false,
                }}
                timechangeHandler={onScrubTime}
                timechangedHandler={onStopScrubbing}
                doubleClickHandler={() => {
                  setSelectedPlayback(timeline);
                }}
                selectHandler={(data) => {
                  if (data.items.length > 0) {
                    const selected = data.items[0];
                    onSelectItem(
                      selectedPlayback.timelineItems.find(
                        (timeline) => timeline.timestamp == selected
                      )
                    );
                  }
                }}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
