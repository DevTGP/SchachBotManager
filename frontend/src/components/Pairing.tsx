import { useTranslation } from "react-i18next";

import { pairing } from "../format/pairing";
import { type Named, SideName } from "./SideName";

/** The header over the three cells of a pairing. */
export function PairingHeader() {
  const { t } = useTranslation();
  return <th colSpan={3}>{t("matchTable.players")}</th>;
}

/**
 * The sides in alphabetical order in cells of their own, so names line up like columns:
 * "Material – Random" whoever had white (E165).
 */
export function PairingCells({ match }: { match: { white: Named; black: Named } }) {
  const { first, second, flipped } = pairing(match);
  return (
    <>
      <td className="pairing-side">
        <SideName side={first} color={flipped ? "b" : "w"} />
      </td>
      <td className="pairing-dash" aria-hidden="true">
        –
      </td>
      <td className="pairing-side">
        <SideName side={second} color={flipped ? "w" : "b"} />
      </td>
    </>
  );
}
