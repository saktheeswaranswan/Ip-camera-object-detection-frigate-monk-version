import SearchThumbnail from "@/components/card/SearchThumbnail";
import SearchFilterGroup from "@/components/filter/SearchFilterGroup";
import ActivityIndicator from "@/components/indicators/activity-indicator";
import Chip from "@/components/indicators/Chip";
import SearchDetailDialog from "@/components/overlay/detail/SearchDetailDialog";
import { Input } from "@/components/ui/input";
import { Toaster } from "@/components/ui/sonner";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { FrigateConfig } from "@/types/frigateConfig";
import { SearchFilter, SearchResult } from "@/types/search";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { isMobileOnly } from "react-device-detect";
import { LuImage, LuSearchX, LuText, LuXCircle } from "react-icons/lu";
import useSWR from "swr";
import ExploreView from "../explore/ExploreView";
import useKeyboardListener, {
  KeyModifiers,
} from "@/hooks/use-keyboard-listener";
import scrollIntoView from "scroll-into-view-if-needed";

type SearchViewProps = {
  search: string;
  searchTerm: string;
  searchFilter?: SearchFilter;
  searchResults?: SearchResult[];
  isLoading: boolean;
  setSearch: (search: string) => void;
  setSimilaritySearch: (search: SearchResult) => void;
  onUpdateFilter: (filter: SearchFilter) => void;
  onOpenSearch: (item: SearchResult) => void;
};
export default function SearchView({
  search,
  searchTerm,
  searchFilter,
  searchResults,
  isLoading,
  setSearch,
  setSimilaritySearch,
  onUpdateFilter,
}: SearchViewProps) {
  const { data: config } = useSWR<FrigateConfig>("config", {
    revalidateOnFocus: false,
  });

  // remove duplicate event ids

  const uniqueResults = useMemo(() => {
    return searchResults?.filter(
      (value, index, self) =>
        index === self.findIndex((v) => v.id === value.id),
    );
  }, [searchResults]);

  // detail

  const [searchDetail, setSearchDetail] = useState<SearchResult>();

  // search interaction

  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);

  const onSelectSearch = useCallback((item: SearchResult, index: number) => {
    setSearchDetail(item);
    setSelectedIndex(index);
  }, []);

  // confidence score - probably needs tweaking

  const zScoreToConfidence = (score: number, source: string) => {
    let midpoint, scale;

    if (source === "thumbnail") {
      midpoint = 2;
      scale = 0.5;
    } else {
      midpoint = 0.5;
      scale = 1.5;
    }

    // Sigmoid function: 1 / (1 + e^x)
    const confidence = 1 / (1 + Math.exp((score - midpoint) * scale));

    return Math.round(confidence * 100);
  };

  const hasExistingSearch = useMemo(
    () => searchResults != undefined || searchFilter != undefined,
    [searchResults, searchFilter],
  );

  // keyboard listener

  const onKeyboardShortcut = useCallback(
    (key: string | null, modifiers: KeyModifiers) => {
      if (!modifiers.down || !uniqueResults) {
        return;
      }

      switch (key) {
        case "ArrowLeft":
          setSelectedIndex((prevIndex) => {
            const newIndex =
              prevIndex === null
                ? uniqueResults.length - 1
                : (prevIndex - 1 + uniqueResults.length) % uniqueResults.length;
            setSearchDetail(uniqueResults[newIndex]);
            return newIndex;
          });
          break;
        case "ArrowRight":
          setSelectedIndex((prevIndex) => {
            const newIndex =
              prevIndex === null ? 0 : (prevIndex + 1) % uniqueResults.length;
            setSearchDetail(uniqueResults[newIndex]);
            return newIndex;
          });
          break;
      }
    },
    [uniqueResults],
  );

  useKeyboardListener(["ArrowLeft", "ArrowRight"], onKeyboardShortcut);

  // scroll into view

  useEffect(() => {
    if (
      selectedIndex !== null &&
      uniqueResults &&
      itemRefs.current?.[selectedIndex]
    ) {
      scrollIntoView(itemRefs.current[selectedIndex], {
        block: "center",
        behavior: "smooth",
        scrollMode: "if-needed",
      });
    }
  }, [selectedIndex, uniqueResults]);

  return (
    <div className="flex size-full flex-col pt-2 md:py-2">
      <Toaster closeButton={true} />
      <SearchDetailDialog
        search={searchDetail}
        setSearch={setSearchDetail}
        setSimilarity={
          searchDetail && (() => setSimilaritySearch(searchDetail))
        }
      />

      <div
        className={cn(
          "flex flex-col items-start space-y-2 pl-2 pr-2 md:mb-2 md:pl-3 lg:h-10 lg:flex-row lg:items-center lg:space-y-0",
          config?.semantic_search?.enabled
            ? "justify-between"
            : "justify-center",
          isMobileOnly && "mb-2 h-auto flex-wrap gap-2 space-y-0",
        )}
      >
        {config?.semantic_search?.enabled && (
          <div
            className={cn(
              "relative w-full",
              hasExistingSearch ? "lg:mr-3 lg:w-1/3" : "lg:ml-[25%] lg:w-1/2",
            )}
          >
            <Input
              className="text-md w-full bg-muted pr-10"
              placeholder={"Search for a tracked object..."}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <LuXCircle
                className="absolute right-2 top-1/2 h-5 w-5 -translate-y-1/2 cursor-pointer text-muted-foreground hover:text-primary"
                onClick={() => setSearch("")}
              />
            )}
          </div>
        )}

        {hasExistingSearch && (
          <SearchFilterGroup
            className={cn(
              "w-full justify-between md:justify-start lg:justify-end",
            )}
            filter={searchFilter}
            searchTerm={searchTerm}
            onUpdateFilter={onUpdateFilter}
          />
        )}
      </div>

      <div className="no-scrollbar flex flex-1 flex-wrap content-start gap-2 overflow-y-auto md:gap-4">
        {searchTerm.length > 0 && searchResults?.length == 0 && (
          <div className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center text-center">
            <LuSearchX className="size-16" />
            No Tracked Objects Found
          </div>
        )}

        {isLoading && (
          <ActivityIndicator className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" />
        )}

        {uniqueResults && (
          <div className="mt-2 grid w-full gap-2 px-1 sm:grid-cols-2 md:mx-2 md:grid-cols-4 md:gap-4 3xl:grid-cols-6">
            {uniqueResults &&
              uniqueResults.map((value, index) => {
                const selected = selectedIndex === index;

                return (
                  <div
                    key={value.id}
                    ref={(item) => (itemRefs.current[index] = item)}
                    data-start={value.start_time}
                    className="review-item relative rounded-lg"
                  >
                    <div
                      className={cn(
                        "aspect-square size-full overflow-hidden rounded-lg",
                      )}
                    >
                      <SearchThumbnail
                        searchResult={value}
                        findSimilar={() => setSimilaritySearch(value)}
                        onClick={() => onSelectSearch(value, index)}
                      />
                      {searchTerm && (
                        <div className={cn("absolute right-2 top-2 z-40")}>
                          <Tooltip>
                            <TooltipTrigger>
                              <Chip
                                className={`flex select-none items-center justify-between space-x-1 bg-gray-500 bg-gradient-to-br from-gray-400 to-gray-500 text-xs capitalize text-white`}
                              >
                                {value.search_source == "thumbnail" ? (
                                  <LuImage className="mr-1 size-3" />
                                ) : (
                                  <LuText className="mr-1 size-3" />
                                )}
                                {zScoreToConfidence(
                                  value.search_distance,
                                  value.search_source,
                                )}
                                %
                              </Chip>
                            </TooltipTrigger>
                            <TooltipContent>
                              Matched {value.search_source} at{" "}
                              {zScoreToConfidence(
                                value.search_distance,
                                value.search_source,
                              )}
                              %
                            </TooltipContent>
                          </Tooltip>
                        </div>
                      )}
                    </div>
                    <div
                      className={`review-item-ring pointer-events-none absolute inset-0 z-10 size-full rounded-lg outline outline-[3px] -outline-offset-[2.8px] ${selected ? `shadow-selected outline-selected` : "outline-transparent duration-500"}`}
                    />
                  </div>
                );
              })}
          </div>
        )}
        {!uniqueResults && !isLoading && (
          <div className="scrollbar-container flex size-full flex-col overflow-y-auto">
            <ExploreView onSelectSearch={onSelectSearch} />
          </div>
        )}
      </div>
    </div>
  );
}
