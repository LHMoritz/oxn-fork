import {
  Gauge,
  MonitorCog,
} from "lucide-react";

export const menuItems = [
  {
    id: "dashboard",
    title: "Dashboard",
    url: "/",
    icon: Gauge,
  },
  {
    id: "experiments",
    title: "Experiments",
    url: "/experiments",
    icon: MonitorCog,
  }
];