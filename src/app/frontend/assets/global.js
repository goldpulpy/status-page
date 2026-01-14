import Alpine from "alpinejs";
import { login } from "./ts/features/auth/login";
import { logout } from "./ts/features/auth/logout";
import { groups } from "./ts/features/admin/groups";
import { monitors } from "./ts/features/admin/monitors";
import { status } from "./ts/features/status";

Alpine.magic("truncate", () => {
  return (text, length = 32) => {
    if (!text) return "";
    return text.length > length ? text.substring(0, length) + "..." : text;
  };
});

Alpine.data("login", login);
Alpine.data("logout", logout);
Alpine.data("groups", groups);
Alpine.data("monitors", monitors);
Alpine.data("status", status);
Alpine.start();
