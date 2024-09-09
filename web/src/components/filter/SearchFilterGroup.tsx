import { Button } from "../ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import useSWR from "swr";
import { FrigateConfig } from "@/types/frigateConfig";
import { useCallback, useMemo, useState } from "react";
import { DropdownMenuSeparator } from "../ui/dropdown-menu";
import { getEndOfDayTimestamp } from "@/utils/dateUtil";
import { FaFilter } from "react-icons/fa";
import { isMobile } from "react-device-detect";
import { Drawer, DrawerContent, DrawerTrigger } from "../ui/drawer";
import { Switch } from "../ui/switch";
import { Label } from "../ui/label";
import FilterSwitch from "./FilterSwitch";
import { FilterList } from "@/types/filter";
import { CalendarRangeFilterButton } from "./CalendarFilterButton";
import { CamerasFilterButton } from "./CamerasFilterButton";
import { SearchFilter, SearchSource } from "@/types/search";
import { DateRange } from "react-day-picker";
import { cn } from "@/lib/utils";
import SubFilterIcon from "../icons/SubFilterIcon";
import { FaLocationDot } from "react-icons/fa6";

const SEARCH_FILTERS = ["cameras", "date", "general", "zone", "sub"] as const;
type SearchFilters = (typeof SEARCH_FILTERS)[number];
const DEFAULT_REVIEW_FILTERS: SearchFilters[] = [
  "cameras",
  "date",
  "general",
  "zone",
  "sub",
];

type SearchFilterGroupProps = {
  className: string;
  filters?: SearchFilters[];
  filter?: SearchFilter;
  filterList?: FilterList;
  onUpdateFilter: (filter: SearchFilter) => void;
};

export default function SearchFilterGroup({
  className,
  filters = DEFAULT_REVIEW_FILTERS,
  filter,
  filterList,
  onUpdateFilter,
}: SearchFilterGroupProps) {
  const { data: config } = useSWR<FrigateConfig>("config", {
    revalidateOnFocus: false,
  });

  const allLabels = useMemo<string[]>(() => {
    if (filterList?.labels) {
      return filterList.labels;
    }

    if (!config) {
      return [];
    }

    const labels = new Set<string>();
    const cameras = filter?.cameras || Object.keys(config.cameras);

    cameras.forEach((camera) => {
      if (camera == "birdseye") {
        return;
      }
      const cameraConfig = config.cameras[camera];
      cameraConfig.objects.track.forEach((label) => {
        labels.add(label);
      });

      if (cameraConfig.audio.enabled_in_config) {
        cameraConfig.audio.listen.forEach((label) => {
          labels.add(label);
        });
      }
    });

    return [...labels].sort();
  }, [config, filterList, filter]);

  const { data: allSubLabels } = useSWR("sub_labels");

  const allZones = useMemo<string[]>(() => {
    if (filterList?.zones) {
      return filterList.zones;
    }

    if (!config) {
      return [];
    }

    const zones = new Set<string>();
    const cameras = filter?.cameras || Object.keys(config.cameras);

    cameras.forEach((camera) => {
      if (camera == "birdseye") {
        return;
      }
      const cameraConfig = config.cameras[camera];
      cameraConfig.review.alerts.required_zones.forEach((zone) => {
        zones.add(zone);
      });
      cameraConfig.review.detections.required_zones.forEach((zone) => {
        zones.add(zone);
      });
    });

    return [...zones].sort();
  }, [config, filterList, filter]);

  const filterValues = useMemo(
    () => ({
      cameras: Object.keys(config?.cameras || {}),
      labels: Object.values(allLabels || {}),
      zones: Object.values(allZones || {}),
      search_type: ["thumbnail", "description"] as SearchSource[],
    }),
    [config, allLabels, allZones],
  );

  const groups = useMemo(() => {
    if (!config) {
      return [];
    }

    return Object.entries(config.camera_groups).sort(
      (a, b) => a[1].order - b[1].order,
    );
  }, [config]);

  // handle updating filters

  const onUpdateSelectedRange = useCallback(
    (range?: DateRange) => {
      onUpdateFilter({
        ...filter,
        after:
          range?.from == undefined ? undefined : range.from.getTime() / 1000,
        before:
          range?.to == undefined ? undefined : getEndOfDayTimestamp(range.to),
      });
    },
    [filter, onUpdateFilter],
  );

  return (
    <div className={cn("flex justify-center gap-2", className)}>
      {filters.includes("cameras") && (
        <CamerasFilterButton
          allCameras={filterValues.cameras}
          groups={groups}
          selectedCameras={filter?.cameras}
          updateCameraFilter={(newCameras) => {
            onUpdateFilter({ ...filter, cameras: newCameras });
          }}
        />
      )}
      {filters.includes("date") && (
        <CalendarRangeFilterButton
          range={
            filter?.after == undefined || filter?.before == undefined
              ? undefined
              : {
                  from: new Date(filter.after * 1000),
                  to: new Date(filter.before * 1000),
                }
          }
          defaultText="All Dates"
          updateSelectedRange={onUpdateSelectedRange}
        />
      )}
      {filters.includes("general") && (
        <GeneralFilterButton
          allLabels={filterValues.labels}
          selectedLabels={filter?.labels}
          selectedSearchSources={
            filter?.search_type ?? ["thumbnail", "description"]
          }
          updateLabelFilter={(newLabels) => {
            onUpdateFilter({ ...filter, labels: newLabels });
          }}
          updateSearchSourceFilter={(newSearchSource) =>
            onUpdateFilter({ ...filter, search_type: newSearchSource })
          }
        />
      )}
      {filters.includes("zone") && allZones.length > 0 && (
        <ZoneFilterButton
          allZones={filterValues.zones}
          selectedZones={filter?.zones}
          updateZoneFilter={(newZones) =>
            onUpdateFilter({ ...filter, zones: newZones })
          }
        />
      )}
      {filters.includes("sub") && (
        <SubFilterButton
          allSubLabels={allSubLabels}
          selectedSubLabels={filter?.subLabels}
          updateSubLabelFilter={(newSubLabels) =>
            onUpdateFilter({ ...filter, subLabels: newSubLabels })
          }
        />
      )}
    </div>
  );
}

type GeneralFilterButtonProps = {
  allLabels: string[];
  selectedLabels: string[] | undefined;
  selectedSearchSources: SearchSource[];
  updateLabelFilter: (labels: string[] | undefined) => void;
  updateSearchSourceFilter: (sources: SearchSource[]) => void;
};
function GeneralFilterButton({
  allLabels,
  selectedLabels,
  selectedSearchSources,
  updateLabelFilter,
  updateSearchSourceFilter,
}: GeneralFilterButtonProps) {
  const [open, setOpen] = useState(false);
  const [currentLabels, setCurrentLabels] = useState<string[] | undefined>(
    selectedLabels,
  );
  const [currentSearchSources, setCurrentSearchSources] = useState<
    SearchSource[]
  >(selectedSearchSources);

  const trigger = (
    <Button
      size="sm"
      variant={selectedLabels?.length ? "select" : "default"}
      className="flex items-center gap-2 capitalize"
    >
      <FaFilter
        className={`${selectedLabels?.length ? "text-selected-foreground" : "text-secondary-foreground"}`}
      />
      <div
        className={`hidden md:block ${selectedLabels?.length ? "text-selected-foreground" : "text-primary"}`}
      >
        Filter
      </div>
    </Button>
  );
  const content = (
    <GeneralFilterContent
      allLabels={allLabels}
      selectedLabels={selectedLabels}
      currentLabels={currentLabels}
      selectedSearchSources={selectedSearchSources}
      currentSearchSources={currentSearchSources}
      setCurrentLabels={setCurrentLabels}
      updateLabelFilter={updateLabelFilter}
      setCurrentSearchSources={setCurrentSearchSources}
      updateSearchSourceFilter={updateSearchSourceFilter}
      onClose={() => setOpen(false)}
    />
  );

  if (isMobile) {
    return (
      <Drawer
        open={open}
        onOpenChange={(open) => {
          if (!open) {
            setCurrentLabels(selectedLabels);
          }

          setOpen(open);
        }}
      >
        <DrawerTrigger asChild>{trigger}</DrawerTrigger>
        <DrawerContent className="max-h-[75dvh] overflow-hidden">
          {content}
        </DrawerContent>
      </Drawer>
    );
  }

  return (
    <Popover
      open={open}
      onOpenChange={(open) => {
        if (!open) {
          setCurrentLabels(selectedLabels);
        }

        setOpen(open);
      }}
    >
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent>{content}</PopoverContent>
    </Popover>
  );
}

type GeneralFilterContentProps = {
  allLabels: string[];
  selectedLabels: string[] | undefined;
  currentLabels: string[] | undefined;
  selectedSearchSources: SearchSource[];
  currentSearchSources: SearchSource[];
  updateLabelFilter: (labels: string[] | undefined) => void;
  setCurrentLabels: (labels: string[] | undefined) => void;
  setCurrentSearchSources: (sources: SearchSource[]) => void;
  updateSearchSourceFilter: (sources: SearchSource[]) => void;
  onClose: () => void;
};
export function GeneralFilterContent({
  allLabels,
  selectedLabels,
  currentLabels,
  selectedSearchSources,
  currentSearchSources,
  updateLabelFilter,
  setCurrentLabels,
  setCurrentSearchSources,
  updateSearchSourceFilter,
  onClose,
}: GeneralFilterContentProps) {
  const { data: config } = useSWR<FrigateConfig>("config", {
    revalidateOnFocus: false,
  });

  return (
    <>
      <div className="scrollbar-container h-auto max-h-[80dvh] overflow-y-auto overflow-x-hidden">
        {config?.semantic_search?.enabled && (
          <div className="my-2.5 flex flex-col gap-2.5">
            <FilterSwitch
              label="Thumbnail Image"
              isChecked={currentSearchSources?.includes("thumbnail") ?? false}
              onCheckedChange={(isChecked) => {
                const updatedSources = currentSearchSources
                  ? [...currentSearchSources]
                  : [];

                if (isChecked) {
                  updatedSources.push("thumbnail");
                  setCurrentSearchSources(updatedSources);
                } else {
                  if (updatedSources.length > 1) {
                    const index = updatedSources.indexOf("thumbnail");
                    if (index !== -1) updatedSources.splice(index, 1);
                    setCurrentSearchSources(updatedSources);
                  }
                }
              }}
            />
            <FilterSwitch
              label="Description"
              isChecked={currentSearchSources?.includes("description") ?? false}
              onCheckedChange={(isChecked) => {
                const updatedSources = currentSearchSources
                  ? [...currentSearchSources]
                  : [];

                if (isChecked) {
                  updatedSources.push("description");
                  setCurrentSearchSources(updatedSources);
                } else {
                  if (updatedSources.length > 1) {
                    const index = updatedSources.indexOf("description");
                    if (index !== -1) updatedSources.splice(index, 1);
                    setCurrentSearchSources(updatedSources);
                  }
                }
              }}
            />
            <DropdownMenuSeparator />
          </div>
        )}
        <div className="mb-5 mt-2.5 flex items-center justify-between">
          <Label
            className="mx-2 cursor-pointer text-primary"
            htmlFor="allLabels"
          >
            All Labels
          </Label>
          <Switch
            className="ml-1"
            id="allLabels"
            checked={currentLabels == undefined}
            onCheckedChange={(isChecked) => {
              if (isChecked) {
                setCurrentLabels(undefined);
              }
            }}
          />
        </div>
        <div className="my-2.5 flex flex-col gap-2.5">
          {allLabels.map((item) => (
            <FilterSwitch
              key={item}
              label={item.replaceAll("_", " ")}
              isChecked={currentLabels?.includes(item) ?? false}
              onCheckedChange={(isChecked) => {
                if (isChecked) {
                  const updatedLabels = currentLabels ? [...currentLabels] : [];

                  updatedLabels.push(item);
                  setCurrentLabels(updatedLabels);
                } else {
                  const updatedLabels = currentLabels ? [...currentLabels] : [];

                  // can not deselect the last item
                  if (updatedLabels.length > 1) {
                    updatedLabels.splice(updatedLabels.indexOf(item), 1);
                    setCurrentLabels(updatedLabels);
                  }
                }
              }}
            />
          ))}
        </div>
      </div>
      <DropdownMenuSeparator />
      <div className="flex items-center justify-evenly p-2">
        <Button
          variant="select"
          onClick={() => {
            if (selectedLabels != currentLabels) {
              updateLabelFilter(currentLabels);
            }

            if (selectedSearchSources != currentSearchSources) {
              updateSearchSourceFilter(currentSearchSources);
            }

            onClose();
          }}
        >
          Apply
        </Button>
        <Button
          onClick={() => {
            setCurrentLabels(undefined);
            updateLabelFilter(undefined);
          }}
        >
          Reset
        </Button>
      </div>
    </>
  );
}

type ZoneFilterButtonProps = {
  allZones: string[];
  selectedZones?: string[];
  updateZoneFilter: (zones: string[] | undefined) => void;
};
function ZoneFilterButton({
  allZones,
  selectedZones,
  updateZoneFilter,
}: ZoneFilterButtonProps) {
  const [open, setOpen] = useState(false);

  const [currentZones, setCurrentZones] = useState<string[] | undefined>(
    selectedZones,
  );

  const trigger = (
    <Button
      size="sm"
      variant={selectedZones?.length ? "select" : "default"}
      className="flex items-center gap-2 capitalize"
    >
      <FaLocationDot
        className={`${selectedZones?.length ? "text-selected-foreground" : "text-secondary-foreground"}`}
      />
      <div
        className={`hidden md:block ${selectedZones?.length ? "text-selected-foreground" : "text-primary"}`}
      >
        {selectedZones?.length ? `${selectedZones.length} Zones` : "All Zones"}
      </div>
    </Button>
  );
  const content = (
    <ZoneFilterContent
      allZones={allZones}
      selectedZones={selectedZones}
      currentZones={currentZones}
      setCurrentZones={setCurrentZones}
      updateZoneFilter={updateZoneFilter}
      onClose={() => setOpen(false)}
    />
  );

  if (isMobile) {
    return (
      <Drawer
        open={open}
        onOpenChange={(open) => {
          if (!open) {
            setCurrentZones(selectedZones);
          }

          setOpen(open);
        }}
      >
        <DrawerTrigger asChild>{trigger}</DrawerTrigger>
        <DrawerContent className="max-h-[75dvh] overflow-hidden">
          {content}
        </DrawerContent>
      </Drawer>
    );
  }

  return (
    <Popover
      open={open}
      onOpenChange={(open) => {
        if (!open) {
          setCurrentZones(selectedZones);
        }

        setOpen(open);
      }}
    >
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent>{content}</PopoverContent>
    </Popover>
  );
}

type ZoneFilterContentProps = {
  allZones?: string[];
  selectedZones?: string[];
  currentZones?: string[];
  updateZoneFilter?: (zones: string[] | undefined) => void;
  setCurrentZones?: (zones: string[] | undefined) => void;
  onClose: () => void;
};
export function ZoneFilterContent({
  allZones,
  selectedZones,
  currentZones,
  updateZoneFilter,
  setCurrentZones,
  onClose,
}: ZoneFilterContentProps) {
  return (
    <>
      <div className="scrollbar-container h-auto max-h-[80dvh] overflow-y-auto overflow-x-hidden">
        {allZones && setCurrentZones && (
          <>
            <DropdownMenuSeparator />
            <div className="mb-5 mt-2.5 flex items-center justify-between">
              <Label
                className="mx-2 cursor-pointer text-primary"
                htmlFor="allZones"
              >
                All Zones
              </Label>
              <Switch
                className="ml-1"
                id="allZones"
                checked={currentZones == undefined}
                onCheckedChange={(isChecked) => {
                  if (isChecked) {
                    setCurrentZones(undefined);
                  }
                }}
              />
            </div>
            <div className="my-2.5 flex flex-col gap-2.5">
              {allZones.map((item) => (
                <FilterSwitch
                  key={item}
                  label={item.replaceAll("_", " ")}
                  isChecked={currentZones?.includes(item) ?? false}
                  onCheckedChange={(isChecked) => {
                    if (isChecked) {
                      const updatedZones = currentZones
                        ? [...currentZones]
                        : [];

                      updatedZones.push(item);
                      setCurrentZones(updatedZones);
                    } else {
                      const updatedZones = currentZones
                        ? [...currentZones]
                        : [];

                      // can not deselect the last item
                      if (updatedZones.length > 1) {
                        updatedZones.splice(updatedZones.indexOf(item), 1);
                        setCurrentZones(updatedZones);
                      }
                    }
                  }}
                />
              ))}
            </div>
          </>
        )}
      </div>
      <DropdownMenuSeparator />
      <div className="flex items-center justify-evenly p-2">
        <Button
          variant="select"
          onClick={() => {
            if (updateZoneFilter && selectedZones != currentZones) {
              updateZoneFilter(currentZones);
            }

            onClose();
          }}
        >
          Apply
        </Button>
        <Button
          onClick={() => {
            setCurrentZones?.(undefined);
          }}
        >
          Reset
        </Button>
      </div>
    </>
  );
}

type SubFilterButtonProps = {
  allSubLabels: string[];
  selectedSubLabels: string[] | undefined;
  updateSubLabelFilter: (labels: string[] | undefined) => void;
};
function SubFilterButton({
  allSubLabels,
  selectedSubLabels,
  updateSubLabelFilter,
}: SubFilterButtonProps) {
  const [open, setOpen] = useState(false);
  const [currentSubLabels, setCurrentSubLabels] = useState<
    string[] | undefined
  >(selectedSubLabels);

  const trigger = (
    <Button
      size="sm"
      variant={selectedSubLabels?.length ? "select" : "default"}
      className="flex items-center gap-2 capitalize"
    >
      <SubFilterIcon
        className={`${selectedSubLabels?.length || selectedSubLabels?.length ? "text-selected-foreground" : "text-secondary-foreground"}`}
      />
      <div
        className={`hidden md:block ${selectedSubLabels?.length ? "text-selected-foreground" : "text-primary"}`}
      >
        {selectedSubLabels?.length
          ? `${selectedSubLabels.length} Sub Labels`
          : "All Sub Labels"}
      </div>
    </Button>
  );
  const content = (
    <SubFilterContent
      allSubLabels={allSubLabels}
      selectedSubLabels={selectedSubLabels}
      currentSubLabels={currentSubLabels}
      setCurrentSubLabels={setCurrentSubLabels}
      updateSubLabelFilter={updateSubLabelFilter}
      onClose={() => setOpen(false)}
    />
  );

  if (isMobile) {
    return (
      <Drawer
        open={open}
        onOpenChange={(open) => {
          if (!open) {
            setCurrentSubLabels(selectedSubLabels);
          }

          setOpen(open);
        }}
      >
        <DrawerTrigger asChild>{trigger}</DrawerTrigger>
        <DrawerContent className="max-h-[75dvh] overflow-hidden">
          {content}
        </DrawerContent>
      </Drawer>
    );
  }

  return (
    <Popover
      open={open}
      onOpenChange={(open) => {
        if (!open) {
          setCurrentSubLabels(selectedSubLabels);
        }

        setOpen(open);
      }}
    >
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent>{content}</PopoverContent>
    </Popover>
  );
}

type SubFilterContentProps = {
  allSubLabels: string[];
  selectedSubLabels: string[] | undefined;
  currentSubLabels: string[] | undefined;
  updateSubLabelFilter: (labels: string[] | undefined) => void;
  setCurrentSubLabels: (labels: string[] | undefined) => void;
  onClose: () => void;
};
export function SubFilterContent({
  allSubLabels,
  selectedSubLabels,
  currentSubLabels,
  updateSubLabelFilter,
  setCurrentSubLabels,
  onClose,
}: SubFilterContentProps) {
  return (
    <>
      <div className="scrollbar-container h-auto max-h-[80dvh] overflow-y-auto overflow-x-hidden">
        <div className="mb-5 mt-2.5 flex items-center justify-between">
          <Label
            className="mx-2 cursor-pointer text-primary"
            htmlFor="allLabels"
          >
            All Sub Labels
          </Label>
          <Switch
            className="ml-1"
            id="allLabels"
            checked={currentSubLabels == undefined}
            onCheckedChange={(isChecked) => {
              if (isChecked) {
                setCurrentSubLabels(undefined);
              }
            }}
          />
        </div>
        <div className="my-2.5 flex flex-col gap-2.5">
          {allSubLabels.map((item) => (
            <FilterSwitch
              key={item}
              label={item.replaceAll("_", " ")}
              isChecked={currentSubLabels?.includes(item) ?? false}
              onCheckedChange={(isChecked) => {
                if (isChecked) {
                  const updatedLabels = currentSubLabels
                    ? [...currentSubLabels]
                    : [];

                  updatedLabels.push(item);
                  setCurrentSubLabels(updatedLabels);
                } else {
                  const updatedLabels = currentSubLabels
                    ? [...currentSubLabels]
                    : [];

                  // can not deselect the last item
                  if (updatedLabels.length > 1) {
                    updatedLabels.splice(updatedLabels.indexOf(item), 1);
                    setCurrentSubLabels(updatedLabels);
                  }
                }
              }}
            />
          ))}
        </div>
      </div>
      <DropdownMenuSeparator />
      <div className="flex items-center justify-evenly p-2">
        <Button
          variant="select"
          onClick={() => {
            if (selectedSubLabels != currentSubLabels) {
              updateSubLabelFilter(currentSubLabels);
            }

            onClose();
          }}
        >
          Apply
        </Button>
        <Button
          onClick={() => {
            setCurrentSubLabels(undefined);
          }}
        >
          Reset
        </Button>
      </div>
    </>
  );
}
