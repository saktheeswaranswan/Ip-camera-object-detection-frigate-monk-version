import { MobilePage, MobilePageContent } from "@/components/mobile/MobilePage";
import { Button } from "@/components/ui/button";
import { Drawer, DrawerContent, DrawerTrigger } from "@/components/ui/drawer";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { isMobile } from "react-device-detect";

type PlatformAwareDialogProps = {
  trigger: JSX.Element;
  content: JSX.Element;
  triggerClassName?: string;
  contentClassName?: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};
export default function PlatformAwareDialog({
  trigger,
  content,
  triggerClassName = "",
  contentClassName = "",
  open,
  onOpenChange,
}: PlatformAwareDialogProps) {
  if (isMobile) {
    return (
      <Drawer open={open} onOpenChange={onOpenChange}>
        <DrawerTrigger asChild>{trigger}</DrawerTrigger>
        <DrawerContent className="max-h-[75dvh] overflow-hidden px-4">
          {content}
        </DrawerContent>
      </Drawer>
    );
  }

  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <PopoverTrigger asChild className={triggerClassName}>
        {trigger}
      </PopoverTrigger>
      <PopoverContent className={contentClassName}>{content}</PopoverContent>
    </Popover>
  );
}

type PlatformAwareSheetProps = {
  trigger: JSX.Element;
  content: JSX.Element;
  triggerClassName?: string;
  contentClassName?: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};
export function PlatformAwareSheet({
  trigger,
  content,
  triggerClassName = "",
  contentClassName = "",
  open,
  onOpenChange,
}: PlatformAwareSheetProps) {
  if (isMobile) {
    return (
      <MobilePage open={open} onOpenChange={onOpenChange}>
        <Button asChild onClick={() => onOpenChange(!open)}>
          {trigger}
        </Button>
        <MobilePageContent className="max-h-[75dvh] overflow-hidden px-4">
          {content}
        </MobilePageContent>
      </MobilePage>
    );
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetTrigger asChild className={triggerClassName}>
        {trigger}
      </SheetTrigger>
      <SheetContent className={contentClassName}>{content}</SheetContent>
    </Sheet>
  );
}
