import type { ComponentType } from 'react';
import {
  AlertTriangle as LcAlertTriangle,
  ArrowLeft as LcArrowLeft,
  ArrowRight as LcArrowRight,
  Bell as LcBell,
  Calendar as LcCalendar,
  Check as LcCheck,
  ChevronDown as LcChevronDown,
  ChevronLeft as LcChevronLeft,
  ChevronRight as LcChevronRight,
  ChevronUp as LcChevronUp,
  Clock as LcClock,
  ExternalLink as LcExternalLink,
  Filter as LcFilter,
  Home as LcHome,
  Info as LcInfo,
  List as LcList,
  Loader2 as LcLoader2,
  LogOut as LcLogOut,
  Mail as LcMail,
  MoreHorizontal as LcMoreHorizontal,
  Pencil as LcPencil,
  Plus as LcPlus,
  Search as LcSearch,
  Settings as LcSettings,
  Trash2 as LcTrash2,
  Users as LcUsers,
  X as LcX,
} from 'lucide-react';

interface IconProps {
  className?: string;
  size?: number;
}

type LucideLike = ComponentType<{
  className?: string;
  size?: string | number;
  strokeWidth?: string | number;
  'aria-hidden'?: boolean;
}>;

/**
 * Factory that standardizes every project icon: a fixed `strokeWidth` (1.6), a
 * per-icon default size, and a `displayName`. This is the ONE icon strategy —
 * never mix raw `lucide-react` imports with these wrapped icons in app code.
 */
export function makeIcon(
  Lc: LucideLike,
  defaultSize: number,
  displayName: string,
): ComponentType<IconProps> {
  const Icon = ({ className, size = defaultSize }: IconProps) => (
    <Lc className={className} size={size} strokeWidth={1.6} aria-hidden />
  );
  Icon.displayName = displayName;
  return Icon;
}

export const Home = makeIcon(LcHome, 18, 'Home');
export const List = makeIcon(LcList, 18, 'List');
export const Users = makeIcon(LcUsers, 18, 'Users');
export const Calendar = makeIcon(LcCalendar, 18, 'Calendar');
export const Settings = makeIcon(LcSettings, 18, 'Settings');
export const Bell = makeIcon(LcBell, 18, 'Bell');
export const Search = makeIcon(LcSearch, 16, 'Search');
export const Plus = makeIcon(LcPlus, 16, 'Plus');
export const Pencil = makeIcon(LcPencil, 16, 'Pencil');
export const Trash = makeIcon(LcTrash2, 16, 'Trash');
export const Filter = makeIcon(LcFilter, 16, 'Filter');
export const Clock = makeIcon(LcClock, 16, 'Clock');
export const Mail = makeIcon(LcMail, 16, 'Mail');
export const MoreHorizontal = makeIcon(LcMoreHorizontal, 16, 'MoreHorizontal');
export const SignOut = makeIcon(LcLogOut, 16, 'SignOut');
export const ChevronDown = makeIcon(LcChevronDown, 16, 'ChevronDown');
export const ChevronUp = makeIcon(LcChevronUp, 16, 'ChevronUp');
export const ChevronLeft = makeIcon(LcChevronLeft, 16, 'ChevronLeft');
export const ChevronRight = makeIcon(LcChevronRight, 16, 'ChevronRight');
export const ArrowLeft = makeIcon(LcArrowLeft, 16, 'ArrowLeft');
export const ArrowRight = makeIcon(LcArrowRight, 16, 'ArrowRight');
export const X = makeIcon(LcX, 16, 'X');
export const Check = makeIcon(LcCheck, 16, 'Check');
export const AlertTriangle = makeIcon(LcAlertTriangle, 16, 'AlertTriangle');
export const Info = makeIcon(LcInfo, 16, 'Info');
export const Spinner = makeIcon(LcLoader2, 16, 'Spinner');
export const ExternalLink = makeIcon(LcExternalLink, 14, 'ExternalLink');
