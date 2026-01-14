import { APIError } from "@/shared/lib/api";
import { notyf } from "@/shared/lib/notyf";

export function handleApiError(error: unknown) {
  if (error instanceof APIError) {
    notyf.error(error.message);
  } else {
    notyf.error("Something went wrong");
  }
}
