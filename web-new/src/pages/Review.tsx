import { useMemo, useState } from "react";
import useSWR from "swr";
import { FrigateConfig } from "@/types/frigateConfig";
import Heading from "@/components/ui/heading";
import ActivityIndicator from "@/components/ui/activity-indicator";
import ReviewCard from "@/components/card/ReviewCard";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { formatUnixTimestampToDateTime } from "@/utils/dateUtil";

export function Review() {
    const { data: config } = useSWR<FrigateConfig>("config");
    const timezone = useMemo(() => config?.ui?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone, [config]);
    const start = useMemo(() => new Date().getTime() / 1000, []);
    const { data: hourlyTimeline } = useSWR<HourlyTimeline>(['timeline/hourly', { timezone }]);
    const { data: allPreviews } = useSWR<Preview[]>(`preview/all/start/${Object.keys(hourlyTimeline || [0])[0]}/end/${start}`);

    // detail levels can be normal, extra, full
    const [detailLevel, setDetailLevel] = useState('normal');

    const timelineCards: CardsData | never[] = useMemo(() => {
        if (!hourlyTimeline) {
          return [];
        }

        const cards: CardsData = {};
        Object.keys(hourlyTimeline)
          .reverse()
          .forEach((hour) => {
            const day = new Date(parseInt(hour) * 1000);
            day.setHours(0, 0, 0, 0);
            const dayKey = (day.getTime() / 1000).toString();
            const source_to_types: {[key: string]: string[]} = {};
            Object.values(hourlyTimeline[hour]).forEach((i) => {
              const time = new Date(i.timestamp * 1000);
              time.setSeconds(0);
              time.setMilliseconds(0);
              const key = `${i.source_id}-${time.getMinutes()}`;
              if (key in source_to_types) {
                source_to_types[key].push(i.class_type);
              } else {
                source_to_types[key] = [i.class_type];
              }
            });

            if (!Object.keys(cards).includes(dayKey)) {
                cards[dayKey] = {};
            }
            cards[dayKey][hour] = {};
            Object.values(hourlyTimeline[hour]).forEach((i) => {
              const time = new Date(i.timestamp * 1000);
              time.setSeconds(0);
              time.setMilliseconds(0);
              const key = `${i.camera}-${time.getMinutes()}`;

              // detail level for saving items
              // detail level determines which timeline items for each moment is returned
              // values can be normal, extra, or full
              // normal: return all items except active / attribute / gone / stationary / visible unless that is the only item.
              // extra: return all items except attribute / gone / visible unless that is the only item
              // full: return all items

              let add = true;
              if (detailLevel == 'normal') {
                if (
                  source_to_types[`${i.source_id}-${time.getMinutes()}`].length > 1 &&
                  ['active', 'attribute', 'gone', 'stationary', 'visible'].includes(i.class_type)
                ) {
                  add = false;
                }
              } else if (detailLevel == 'extra') {
                if (
                  source_to_types[`${i.source_id}-${time.getMinutes()}`].length > 1 &&
                  i.class_type in ['attribute', 'gone', 'visible']
                ) {
                  add = false;
                }
              }

              if (add) {
                if (key in cards[dayKey][hour]) {
                  cards[dayKey][hour][key].entries.push(i);
                } else {
                  cards[dayKey][hour][key] = {
                    camera: i.camera,
                    time: time.getTime() / 1000,
                    entries: [i],
                  };
                }
              }
            });
          });

        return cards;
    }, [detailLevel, hourlyTimeline]);

    if (!config || !timelineCards) {
      return <ActivityIndicator />;
    }

    return (
        <>
            <Heading as="h2">Review</Heading>
            <div className="text-xs mb-4">Dates and times are based on the timezone {timezone}</div>

            <div>
                {Object.keys(timelineCards).reverse().map((day) => {
                    return (
                        <div key={day}>
                            <Heading as="h3">
                                {formatUnixTimestampToDateTime(parseInt(day), { strftime_fmt: '%A %b %d' })}
                            </Heading>
                            {Object.entries(timelineCards[day]).map(([hour, timelineHour]) => {
                                return (
                                    <div key={hour}>
                                        <Heading as="h4">
                                            {formatUnixTimestampToDateTime(parseInt(hour), { strftime_fmt: '%I:00' })}
                                        </Heading>
                                        <ScrollArea>
                                            <div className="flex">
                                                {Object.entries(timelineHour).map(([key, timeline]) => {
                                                    return <ReviewCard key={key} timeline={timeline} allPreviews={allPreviews} />
                                                })}
                                            </div>
                                            <ScrollBar className="m-2" orientation="horizontal" />
                                        </ScrollArea>
                                    </div>
                                );
                            })}
                        </div>
                    );
                })}
            </div>
        </>
    );
}

export default Review