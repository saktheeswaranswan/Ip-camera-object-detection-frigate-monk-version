import {
  LuActivity,
  LuGithub,
  LuHardDrive,
  LuLifeBuoy,
  LuList,
  LuMoon,
  LuPenSquare,
  LuRotateCw,
  LuSettings,
  LuSun,
  LuSunMoon,
} from "react-icons/lu";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { Button } from "../ui/button";
import { Link } from "react-router-dom";
import { CgDarkMode } from "react-icons/cg";
import {
  colorSchemes,
  friendlyColorSchemeName,
  useTheme,
} from "@/context/theme-provider";
import { IoColorPalette } from "react-icons/io5";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";
import { useEffect, useState } from "react";
import { useRestart } from "@/api/ws";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "../ui/sheet";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import ActivityIndicator from "../indicators/activity-indicator";
import { isDesktop } from "react-device-detect";
import { Drawer, DrawerContent, DrawerTrigger } from "../ui/drawer";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { PopoverPortal } from "@radix-ui/react-popover";
import { DialogClose } from "../ui/dialog";

type GeneralSettings = {
  className?: string;
};
export default function GeneralSettings({ className }: GeneralSettings) {
  const { theme, colorScheme, setTheme, setColorScheme } = useTheme();
  const [restartDialogOpen, setRestartDialogOpen] = useState(false);
  const [restartingSheetOpen, setRestartingSheetOpen] = useState(false);
  const [countdown, setCountdown] = useState(60);

  const { send: sendRestart } = useRestart();

  useEffect(() => {
    let countdownInterval: NodeJS.Timeout;

    if (restartingSheetOpen) {
      countdownInterval = setInterval(() => {
        setCountdown((prevCountdown) => prevCountdown - 1);
      }, 1000);
    }

    return () => {
      clearInterval(countdownInterval);
    };
  }, [restartingSheetOpen]);

  useEffect(() => {
    if (countdown === 0) {
      window.location.href = "/";
    }
  }, [countdown]);

  const handleForceReload = () => {
    window.location.href = "/";
  };

  const Container = isDesktop ? DropdownMenu : Drawer;
  const Trigger = isDesktop ? DropdownMenuTrigger : DrawerTrigger;
  const Content = isDesktop ? DropdownMenuContent : DrawerContent;
  const MenuItem = isDesktop ? DropdownMenuItem : DialogClose;
  const SubItem = isDesktop ? DropdownMenuSub : Popover;
  const SubItemTrigger = isDesktop ? DropdownMenuSubTrigger : PopoverTrigger;
  const SubItemContent = isDesktop ? DropdownMenuSubContent : PopoverContent;
  const Portal = isDesktop ? DropdownMenuPortal : PopoverPortal;

  return (
    <>
      <div className={className}>
        <Container>
          <Trigger asChild>
            <a href="#">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button size="icon" variant="ghost">
                    <LuSettings />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <p>Settings</p>
                </TooltipContent>
              </Tooltip>
            </a>
          </Trigger>
          <Content className={isDesktop ? "w-72 mr-5" : "max-h-[75dvh]"}>
            <DropdownMenuLabel>System</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuGroup className={isDesktop ? "" : "flex flex-col"}>
              <Link to="/storage">
                <MenuItem
                  className={
                    isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                  }
                >
                  <LuHardDrive className="mr-2 size-4" />
                  <span>Storage</span>
                </MenuItem>
              </Link>
              <Link to="/system">
                <MenuItem
                  className={
                    isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                  }
                >
                  <LuActivity className="mr-2 size-4" />
                  <span>System metrics</span>
                </MenuItem>
              </Link>
              <Link to="/logs">
                <MenuItem
                  className={
                    isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                  }
                >
                  <LuList className="mr-2 size-4" />
                  <span>System logs</span>
                </MenuItem>
              </Link>
            </DropdownMenuGroup>
            <DropdownMenuLabel className="mt-3">
              Configuration
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <Link to="/settings">
                <MenuItem
                  className={
                    isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                  }
                >
                  <LuSettings className="mr-2 size-4" />
                  <span>Settings</span>
                </MenuItem>
              </Link>
              <Link to="/config">
                <MenuItem
                  className={
                    isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                  }
                >
                  <LuPenSquare className="mr-2 size-4" />
                  <span>Configuration editor</span>
                </MenuItem>
              </Link>
              <DropdownMenuLabel className="mt-3">Appearance</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <SubItem>
                <SubItemTrigger
                  className={
                    isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                  }
                >
                  <LuSunMoon className="mr-2 size-4" />
                  <span>Dark Mode</span>
                </SubItemTrigger>
                <Portal>
                  <SubItemContent>
                    <MenuItem
                      className={
                        isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                      }
                      onClick={() => setTheme("light")}
                    >
                      {theme === "light" ? (
                        <>
                          <LuSun className="mr-2 size-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                          Light
                        </>
                      ) : (
                        <span className="mr-2 ml-6">Light</span>
                      )}
                    </MenuItem>
                    <MenuItem
                      className={
                        isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                      }
                      onClick={() => setTheme("dark")}
                    >
                      {theme === "dark" ? (
                        <>
                          <LuMoon className="mr-2 size-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                          Dark
                        </>
                      ) : (
                        <span className="mr-2 ml-6">Dark</span>
                      )}
                    </MenuItem>
                    <MenuItem
                      className={
                        isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                      }
                      onClick={() => setTheme("system")}
                    >
                      {theme === "system" ? (
                        <>
                          <CgDarkMode className="mr-2 size-4 scale-100 transition-all" />
                          System
                        </>
                      ) : (
                        <span className="mr-2 ml-6">System</span>
                      )}
                    </MenuItem>
                  </SubItemContent>
                </Portal>
              </SubItem>
              <SubItem>
                <SubItemTrigger
                  className={
                    isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                  }
                >
                  <LuSunMoon className="mr-2 size-4" />
                  <span>Theme</span>
                </SubItemTrigger>
                <Portal>
                  <SubItemContent>
                    {colorSchemes.map((scheme) => (
                      <MenuItem
                        key={scheme}
                        className={
                          isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                        }
                        onClick={() => setColorScheme(scheme)}
                      >
                        {scheme === colorScheme ? (
                          <>
                            <IoColorPalette className="mr-2 size-4 rotate-0 scale-100 transition-all" />
                            {friendlyColorSchemeName(scheme)}
                          </>
                        ) : (
                          <span className="mr-2 ml-6">
                            {friendlyColorSchemeName(scheme)}
                          </span>
                        )}
                      </MenuItem>
                    ))}
                  </SubItemContent>
                </Portal>
              </SubItem>
            </DropdownMenuGroup>
            <DropdownMenuLabel className="mt-3">Help</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <a href="https://docs.frigate.video">
              <MenuItem
                className={
                  isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                }
              >
                <LuLifeBuoy className="mr-2 size-4" />
                <span>Documentation</span>
              </MenuItem>
            </a>
            <a href="https://github.com/blakeblackshear/frigate">
              <MenuItem
                className={
                  isDesktop ? "cursor-pointer" : "p-2 flex items-center"
                }
              >
                <LuGithub className="mr-2 size-4" />
                <span>GitHub</span>
              </MenuItem>
            </a>
            <DropdownMenuSeparator className="mt-3" />
            <MenuItem
              className={isDesktop ? "cursor-pointer" : "p-2 flex items-center"}
              onClick={() => setRestartDialogOpen(true)}
            >
              <LuRotateCw className="mr-2 size-4" />
              <span>Restart Frigate</span>
            </MenuItem>
          </Content>
        </Container>
      </div>
      {restartDialogOpen && (
        <AlertDialog
          open={restartDialogOpen}
          onOpenChange={() => setRestartDialogOpen(false)}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>
                Are you sure you want to restart Frigate?
              </AlertDialogTitle>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => {
                  setRestartingSheetOpen(true);
                  sendRestart("restart");
                }}
              >
                Restart
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
      {restartingSheetOpen && (
        <>
          <Sheet
            open={restartingSheetOpen}
            onOpenChange={() => setRestartingSheetOpen(false)}
          >
            <SheetContent
              side="top"
              onInteractOutside={(e) => e.preventDefault()}
            >
              <div className="flex flex-col items-center">
                <ActivityIndicator />
                <SheetHeader className="mt-5 text-center">
                  <SheetTitle className="text-center">
                    Frigate is Restarting
                  </SheetTitle>
                  <SheetDescription className="text-center">
                    <p>This page will reload in {countdown} seconds.</p>
                  </SheetDescription>
                </SheetHeader>
                <Button size="lg" className="mt-5" onClick={handleForceReload}>
                  Force Reload Now
                </Button>
              </div>
            </SheetContent>
          </Sheet>
        </>
      )}
    </>
  );
}
