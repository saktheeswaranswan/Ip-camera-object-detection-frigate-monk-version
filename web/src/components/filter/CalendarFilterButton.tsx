import {
  useFormattedRange,
  useFormattedTimestamp,
} from "@/hooks/use-date-utils";
import { ReviewSummary } from "@/types/review";
import { Button } from "../ui/button";
import { FaCalendarAlt } from "react-icons/fa";
import ReviewActivityCalendar from "../overlay/ReviewActivityCalendar";
import { DropdownMenuSeparator } from "../ui/dropdown-menu";
import { Drawer, DrawerContent, DrawerTrigger } from "../ui/drawer";
import { isMobile } from "react-device-detect";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { DateRangePicker } from "../ui/calendar-range";
import { DateRange } from "react-day-picker";

type CalendarFilterButtonProps = {
  reviewSummary?: ReviewSummary;
  day?: Date;
  defaultText: string;
  updateSelectedDay: (day?: Date) => void;
};
export default function CalendarFilterButton({
  reviewSummary,
  day,
  defaultText,
  updateSelectedDay,
}: CalendarFilterButtonProps) {
  const selectedDate = useFormattedTimestamp(
    day == undefined ? 0 : day?.getTime() / 1000 + 1,
    "%b %-d",
  );

  const trigger = (
    <Button
      className="flex items-center gap-2"
      variant={day == undefined ? "default" : "select"}
      size="sm"
    >
      <FaCalendarAlt
        className={`${day == undefined ? "text-secondary-foreground" : "text-selected-foreground"}`}
      />
      <div
        className={`hidden md:block ${day == undefined ? "text-primary" : "text-selected-foreground"}`}
      >
        {day == undefined ? defaultText : selectedDate}
      </div>
    </Button>
  );
  const content = (
    <>
      <ReviewActivityCalendar
        reviewSummary={reviewSummary}
        selectedDay={day}
        onSelect={updateSelectedDay}
      />
      <DropdownMenuSeparator />
      <div className="flex items-center justify-center p-2">
        <Button
          onClick={() => {
            updateSelectedDay(undefined);
          }}
        >
          Reset
        </Button>
      </div>
    </>
  );

  if (isMobile) {
    return (
      <Drawer>
        <DrawerTrigger asChild>{trigger}</DrawerTrigger>
        <DrawerContent>{content}</DrawerContent>
      </Drawer>
    );
  }

  return (
    <Popover>
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent>{content}</PopoverContent>
    </Popover>
  );
}

type CalendarRangeFilterButtonProps = {
  range?: DateRange;
  defaultText: string;
  updateSelectedRange: (range?: DateRange) => void;
};
export function CalendarRangeFilterButton({
  range,
  defaultText,
  updateSelectedRange,
}: CalendarRangeFilterButtonProps) {
  const selectedDate = useFormattedRange(
    range?.from == undefined ? 0 : range.from.getTime() / 1000 + 1,
    range?.to == undefined ? 0 : range.to.getTime() / 1000 - 1,
    "%b %-d",
  );

  const trigger = (
    <Button
      className="flex items-center gap-2"
      variant={range == undefined ? "default" : "select"}
      size="sm"
    >
      <FaCalendarAlt
        className={`${range == undefined ? "text-secondary-foreground" : "text-selected-foreground"}`}
      />
      <div
        className={`hidden md:block ${range == undefined ? "text-primary" : "text-selected-foreground"}`}
      >
        {range == undefined ? defaultText : selectedDate}
      </div>
    </Button>
  );
  const content = (
    <>
      <DateRangePicker
        initialDateFrom={range?.from}
        initialDateTo={range?.to}
        showCompare={false}
        onUpdate={(range) => updateSelectedRange(range.range)}
      />
      <DropdownMenuSeparator />
      <div className="flex items-center justify-center p-2">
        <Button
          onClick={() => {
            updateSelectedRange(undefined);
          }}
        >
          Reset
        </Button>
      </div>
    </>
  );

  if (isMobile) {
    return (
      <Drawer>
        <DrawerTrigger asChild>{trigger}</DrawerTrigger>
        <DrawerContent>{content}</DrawerContent>
      </Drawer>
    );
  }

  return (
    <Popover>
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent className="w-[840px]">{content}</PopoverContent>
    </Popover>
  );
}
