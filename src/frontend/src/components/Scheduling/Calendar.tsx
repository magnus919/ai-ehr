import { useState, useMemo, useCallback } from 'react';
import {
  format,
  startOfWeek,
  addDays,
  addWeeks,
  subWeeks,
  isSameDay,
  parseISO,
  setHours,
  setMinutes,
  isToday,
} from 'date-fns';
import {
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { useAppointmentsForRange } from '@/hooks/useAppointments';
import { formatTime } from '@/utils/formatters';
import {
  APPOINTMENT_STATUS_COLORS,
  APPOINTMENT_STATUS_LABELS,
  APPOINTMENT_TYPE_LABELS,
} from '@/utils/constants';
import type { Appointment, UUID } from '@/types';

// -----------------------------------------------------------------------------
// Calendar Component
// -----------------------------------------------------------------------------

interface CalendarProps {
  /** Selected provider ID for filtering */
  providerId?: UUID;
  /** Called when an appointment is clicked */
  onAppointmentClick?: (appointment: Appointment) => void;
  /** Called when a time slot is clicked to create a new appointment */
  onSlotClick?: (date: Date) => void;
}

type CalendarView = 'week' | 'day';

const HOURS = Array.from({ length: 12 }, (_, i) => i + 7); // 7 AM to 6 PM
const SLOT_HEIGHT = 60; // px per hour

export function Calendar({
  providerId,
  onAppointmentClick,
  onSlotClick,
}: CalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<CalendarView>('week');

  const weekStart = useMemo(
    () => startOfWeek(currentDate, { weekStartsOn: 1 }),
    [currentDate],
  );

  const days = useMemo(() => {
    if (view === 'day') return [currentDate];
    return Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
  }, [currentDate, weekStart, view]);

  const startDate = format(days[0], 'yyyy-MM-dd');
  const endDate = format(days[days.length - 1], 'yyyy-MM-dd');

  const { data: appointments, isLoading } = useAppointmentsForRange(
    startDate,
    endDate,
    providerId,
  );

  // ---------------------------------------------------------------------------
  // Navigation
  // ---------------------------------------------------------------------------

  const goBack = useCallback(() => {
    if (view === 'week') {
      setCurrentDate((d) => subWeeks(d, 1));
    } else {
      setCurrentDate((d) => addDays(d, -1));
    }
  }, [view]);

  const goForward = useCallback(() => {
    if (view === 'week') {
      setCurrentDate((d) => addWeeks(d, 1));
    } else {
      setCurrentDate((d) => addDays(d, 1));
    }
  }, [view]);

  const goToToday = useCallback(() => {
    setCurrentDate(new Date());
  }, []);

  // ---------------------------------------------------------------------------
  // Map appointments to days
  // ---------------------------------------------------------------------------

  const appointmentsByDay = useMemo(() => {
    const map = new Map<string, Appointment[]>();
    appointments?.forEach((apt) => {
      const dayKey = format(parseISO(apt.start), 'yyyy-MM-dd');
      if (!map.has(dayKey)) map.set(dayKey, []);
      map.get(dayKey)!.push(apt);
    });
    return map;
  }, [appointments]);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="flex flex-col rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      {/* Calendar Header */}
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {view === 'week'
              ? `${format(days[0], 'MMM d')} - ${format(days[days.length - 1], 'MMM d, yyyy')}`
              : format(currentDate, 'EEEE, MMMM d, yyyy')}
          </h2>
          {isLoading && <LoadingSpinner size="sm" />}
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={goToToday}
            className="btn-secondary text-xs"
          >
            Today
          </button>
          <div className="flex rounded-md border border-gray-300 dark:border-gray-600">
            <button
              type="button"
              onClick={goBack}
              className="rounded-l-md px-2 py-1.5 text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
              aria-label={view === 'week' ? 'Previous week' : 'Previous day'}
            >
              <ChevronLeftIcon className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={goForward}
              className="rounded-r-md px-2 py-1.5 text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
              aria-label={view === 'week' ? 'Next week' : 'Next day'}
            >
              <ChevronRightIcon className="h-4 w-4" />
            </button>
          </div>
          <div className="flex rounded-md border border-gray-300 dark:border-gray-600">
            <button
              type="button"
              onClick={() => setView('day')}
              className={clsx(
                'rounded-l-md px-3 py-1.5 text-xs font-medium',
                view === 'day'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700',
              )}
            >
              Day
            </button>
            <button
              type="button"
              onClick={() => setView('week')}
              className={clsx(
                'rounded-r-md px-3 py-1.5 text-xs font-medium',
                view === 'week'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700',
              )}
            >
              Week
            </button>
          </div>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="flex overflow-x-auto">
        {/* Time Gutter */}
        <div className="flex-shrink-0 border-r border-gray-200 dark:border-gray-700">
          <div className="h-12 border-b border-gray-200 dark:border-gray-700" />
          {HOURS.map((hour) => (
            <div
              key={hour}
              className="flex h-[60px] items-start justify-end border-b border-gray-100 pr-2 pt-0 dark:border-gray-700"
            >
              <span className="relative -top-2 text-2xs text-gray-400">
                {format(setMinutes(setHours(new Date(), hour), 0), 'h a')}
              </span>
            </div>
          ))}
        </div>

        {/* Day Columns */}
        {days.map((day) => {
          const dayKey = format(day, 'yyyy-MM-dd');
          const dayAppointments = appointmentsByDay.get(dayKey) ?? [];

          return (
            <div
              key={dayKey}
              className={clsx(
                'flex-1 min-w-[120px] border-r border-gray-200 dark:border-gray-700 last:border-r-0',
                isToday(day) && 'bg-primary-50/30 dark:bg-primary-950/10',
              )}
            >
              {/* Day Header */}
              <div
                className={clsx(
                  'sticky top-0 z-10 flex h-12 flex-col items-center justify-center border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800',
                  isToday(day) && 'bg-primary-50 dark:bg-primary-950/20',
                )}
              >
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {format(day, 'EEE')}
                </span>
                <span
                  className={clsx(
                    'text-sm font-semibold',
                    isToday(day)
                      ? 'text-primary-600 dark:text-primary-400'
                      : 'text-gray-900 dark:text-gray-100',
                  )}
                >
                  {format(day, 'd')}
                </span>
              </div>

              {/* Time Slots */}
              <div className="relative">
                {HOURS.map((hour) => (
                  <div
                    key={hour}
                    className="h-[60px] border-b border-gray-100 dark:border-gray-700"
                    onClick={() => {
                      const slotDate = setMinutes(setHours(day, hour), 0);
                      onSlotClick?.(slotDate);
                    }}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        const slotDate = setMinutes(setHours(day, hour), 0);
                        onSlotClick?.(slotDate);
                      }
                    }}
                    aria-label={`${format(day, 'EEEE MMM d')} at ${hour}:00. Click to add appointment.`}
                  />
                ))}

                {/* Appointment Blocks */}
                {dayAppointments.map((apt) => {
                  const start = parseISO(apt.start);
                  const startHour = start.getHours() + start.getMinutes() / 60;
                  const top = (startHour - HOURS[0]) * SLOT_HEIGHT;
                  const height = (apt.minutesDuration / 60) * SLOT_HEIGHT;

                  return (
                    <button
                      key={apt.id}
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onAppointmentClick?.(apt);
                      }}
                      className={clsx(
                        'absolute left-1 right-1 overflow-hidden rounded-md border-l-4 px-2 py-1 text-left text-xs shadow-sm transition-shadow hover:shadow-md',
                        'bg-white dark:bg-gray-700',
                        apt.status === 'booked' && 'border-l-blue-500',
                        apt.status === 'arrived' && 'border-l-teal-500',
                        apt.status === 'checked-in' && 'border-l-green-500',
                        apt.status === 'cancelled' && 'border-l-red-500 opacity-50',
                        apt.status === 'noshow' && 'border-l-red-500 opacity-50',
                        apt.status === 'fulfilled' && 'border-l-gray-400',
                      )}
                      style={{
                        top: `${Math.max(0, top)}px`,
                        height: `${Math.max(20, height - 2)}px`,
                      }}
                      aria-label={`${apt.patient.display} - ${formatTime(apt.start)} ${APPOINTMENT_TYPE_LABELS[apt.appointmentType]}`}
                    >
                      <p className="truncate font-medium text-gray-900 dark:text-gray-100">
                        {apt.patient.display}
                      </p>
                      <p className="truncate text-gray-500 dark:text-gray-400">
                        {formatTime(apt.start)} &middot;{' '}
                        {APPOINTMENT_TYPE_LABELS[apt.appointmentType]}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
