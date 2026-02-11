import { useState, useCallback, useRef, useEffect } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { usePatientSearch } from '@/hooks/usePatients';
import { formatNameLastFirst, formatDate, calculateAge } from '@/utils/formatters';
import type { Patient } from '@/types';

// -----------------------------------------------------------------------------
// PatientSearch Component
// -----------------------------------------------------------------------------

interface PatientSearchProps {
  /** Called when a search query is submitted */
  onSearch?: (query: string) => void;
  /** Called when a patient is selected from autocomplete */
  onSelect?: (patient: Patient) => void;
  /** Placeholder text */
  placeholder?: string;
  /** Show autocomplete dropdown */
  showAutocomplete?: boolean;
}

export function PatientSearch({
  onSearch,
  onSelect,
  placeholder = 'Search by name, MRN, or date of birth...',
  showAutocomplete = false,
}: PatientSearchProps) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: searchResults, isLoading } = usePatientSearch(
    showAutocomplete ? query : '',
  );

  const patients = searchResults?.items ?? [];

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      setIsOpen(false);
      onSearch?.(query);
    },
    [query, onSearch],
  );

  const handleSelect = useCallback(
    (patient: Patient) => {
      setQuery(formatNameLastFirst(patient.name));
      setIsOpen(false);
      onSelect?.(patient);
    },
    [onSelect],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen || patients.length === 0) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev < patients.length - 1 ? prev + 1 : 0,
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev > 0 ? prev - 1 : patients.length - 1,
          );
          break;
        case 'Enter':
          if (highlightedIndex >= 0 && highlightedIndex < patients.length) {
            e.preventDefault();
            handleSelect(patients[highlightedIndex]);
          }
          break;
        case 'Escape':
          setIsOpen(false);
          setHighlightedIndex(-1);
          break;
      }
    },
    [isOpen, patients, highlightedIndex, handleSelect],
  );

  return (
    <div ref={wrapperRef} className="relative">
      <form onSubmit={handleSubmit}>
        <label htmlFor="patient-search" className="sr-only">
          Search patients
        </label>
        <div className="relative">
          <MagnifyingGlassIcon
            className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400"
            aria-hidden="true"
          />
          <input
            ref={inputRef}
            id="patient-search"
            type="search"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              if (showAutocomplete && e.target.value.length >= 2) {
                setIsOpen(true);
                setHighlightedIndex(-1);
              } else {
                setIsOpen(false);
              }
            }}
            onKeyDown={handleKeyDown}
            onFocus={() => {
              if (showAutocomplete && query.length >= 2 && patients.length > 0) {
                setIsOpen(true);
              }
            }}
            placeholder={placeholder}
            className="input-base pl-10"
            role={showAutocomplete ? 'combobox' : undefined}
            aria-expanded={showAutocomplete ? isOpen : undefined}
            aria-controls={showAutocomplete ? 'patient-search-results' : undefined}
            aria-activedescendant={
              highlightedIndex >= 0
                ? `patient-option-${highlightedIndex}`
                : undefined
            }
            aria-autocomplete={showAutocomplete ? 'list' : undefined}
          />
        </div>
      </form>

      {/* Autocomplete Dropdown */}
      {showAutocomplete && isOpen && (
        <ul
          id="patient-search-results"
          role="listbox"
          className="absolute z-20 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 shadow-lg ring-1 ring-black/5 dark:bg-gray-800 dark:ring-gray-700"
        >
          {isLoading ? (
            <li className="px-4 py-3 text-sm text-gray-500">Searching...</li>
          ) : patients.length === 0 ? (
            <li className="px-4 py-3 text-sm text-gray-500">
              No patients found for &ldquo;{query}&rdquo;
            </li>
          ) : (
            patients.map((patient, index) => (
              <li
                key={patient.id}
                id={`patient-option-${index}`}
                role="option"
                aria-selected={highlightedIndex === index}
                className={`cursor-pointer px-4 py-3 text-sm ${
                  highlightedIndex === index
                    ? 'bg-primary-50 text-primary-700 dark:bg-primary-950/30 dark:text-primary-300'
                    : 'text-gray-900 hover:bg-gray-50 dark:text-gray-100 dark:hover:bg-gray-700'
                }`}
                onMouseEnter={() => setHighlightedIndex(index)}
                onClick={() => handleSelect(patient)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">
                      {formatNameLastFirst(patient.name)}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      MRN: {patient.mrn} &middot; DOB: {formatDate(patient.birthDate)}
                      {calculateAge(patient.birthDate) !== null &&
                        ` (${calculateAge(patient.birthDate)} yo)`}
                    </p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {patient.gender}
                  </span>
                </div>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
