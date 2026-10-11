import { fetchOwnBots } from "../api/bots";
import { fetchBots } from "../api/endpoints";
import { useSession } from "../session/sessionContext";
import { useApi } from "./useApi";

/**
 * The bots the logged-in account may register in a league or tournament: admins any bot,
 * reference bots included, coders their own (E181).
 */
export function useRegistrableBots() {
  const { user } = useSession();
  const isAdmin = user?.role === "admin";
  return useApi(isAdmin ? fetchBots : fetchOwnBots, isAdmin ? "bots" : "account/bots");
}
