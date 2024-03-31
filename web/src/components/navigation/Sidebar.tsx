import Logo from "../Logo";
import { navbarLinks } from "@/pages/site-navigation";
import SettingsNavItems from "../settings/SettingsNavItems";
import NavItem from "./NavItem";
import { CameraGroupSelector } from "../filter/CameraGroupSelector";
import { useLocation } from "react-router-dom";
import GeneralSettings from "../settings/GeneralSettings";
import AccountSettings from "../settings/AccountSettings";

function Sidebar() {
  const location = useLocation();

  return (
    <aside className="absolute w-[52px] z-10 left-o inset-y-0 overflow-y-auto scrollbar-hidden py-4 flex flex-col justify-between bg-primary border-r border-secondary-highlight">
      <span tabIndex={0} className="sr-only" />
      <div className="w-full flex flex-col gap-0 items-center">
        <Logo className="w-8 h-8 mb-6" />
        {navbarLinks.map((item) => {
          const showCameraGroups =
            item.id == 1 && item.url == location.pathname;

          return (
            <div key={item.id}>
              <NavItem
                className={`mx-[10px] ${showCameraGroups ? "mb-2" : "mb-4"}`}
                Icon={item.icon}
                title={item.title}
                url={item.url}
                dev={item.dev}
              />
              {showCameraGroups && <CameraGroupSelector className="mb-4" />}
            </div>
          );
        })}
      </div>
      <div className="flex flex-col items-center mb-8">
        <GeneralSettings />
        <AccountSettings />
      </div>
    </aside>
  );
}

export default Sidebar;
