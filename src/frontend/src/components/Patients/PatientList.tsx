import { useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon, FunnelIcon } from '@heroicons/react/24/outline';
import { UsersIcon } from '@heroicons/react/24/solid';
import { DataTable, type Column } from '@/components/Common/DataTable';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { PatientSearch } from './PatientSearch';
import { usePatients } from '@/hooks/usePatients';
import { formatNameLastFirst, formatDate, calculateAge } from '@/utils/formatters';
import { GENDER_LABELS, DEFAULT_PAGE_SIZE } from '@/utils/constants';
import type { Patient, PatientSearchParams, Gender } from '@/types';

// -----------------------------------------------------------------------------
// PatientList Component
// -----------------------------------------------------------------------------

export function PatientList() {
  const navigate = useNavigate();

  const [searchParams, setSearchParams] = useState<PatientSearchParams>({
    page: 1,
    pageSize: DEFAULT_PAGE_SIZE,
    sortBy: 'name',
    sortOrder: 'asc',
  });

  const [showFilters, setShowFilters] = useState(false);

  const { data, isLoading } = usePatients(searchParams);

  // ---------------------------------------------------------------------------
  // Column Definitions
  // ---------------------------------------------------------------------------

  const columns: Column<Patient>[] = useMemo(
    () => [
      {
        key: 'mrn',
        header: 'MRN',
        sortable: true,
        width: 'w-28',
        render: (patient) => (
          <span className="font-mono text-xs text-gray-600 dark:text-gray-400">
            {patient.mrn}
          </span>
        ),
      },
      {
        key: 'name',
        header: 'Name',
        sortable: true,
        render: (patient) => (
          <div>
            <p className="font-medium text-gray-900 dark:text-gray-100">
              {formatNameLastFirst(patient.name)}
            </p>
          </div>
        ),
      },
      {
        key: 'birthDate',
        header: 'Date of Birth',
        sortable: true,
        render: (patient) => {
          const age = calculateAge(patient.birthDate);
          return (
            <div>
              <p className="text-gray-900 dark:text-gray-100">
                {formatDate(patient.birthDate)}
              </p>
              {age !== null && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {age} years old
                </p>
              )}
            </div>
          );
        },
      },
      {
        key: 'gender',
        header: 'Gender',
        sortable: true,
        render: (patient) => (
          <span>{GENDER_LABELS[patient.gender] ?? patient.gender}</span>
        ),
      },
      {
        key: 'phone',
        header: 'Phone',
        render: (patient) => {
          const phone = patient.telecom?.find((t) => t.system === 'phone');
          return <span>{phone?.value ?? '--'}</span>;
        },
      },
      {
        key: 'status',
        header: 'Status',
        render: (patient) => (
          <StatusBadge
            label={patient.active ? 'Active' : 'Inactive'}
            color={patient.active ? 'green' : 'gray'}
            dot
          />
        ),
      },
    ],
    [],
  );

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleSort = useCallback(
    (key: string, order: 'asc' | 'desc') => {
      setSearchParams((prev) => ({ ...prev, sortBy: key, sortOrder: order, page: 1 }));
    },
    [],
  );

  const handlePageChange = useCallback((page: number) => {
    setSearchParams((prev) => ({ ...prev, page }));
  }, []);

  const handleRowClick = useCallback(
    (patient: Patient) => {
      navigate(`/patients/${patient.id}`);
    },
    [navigate],
  );

  const handleSearch = useCallback((query: string) => {
    setSearchParams((prev) => ({ ...prev, query, page: 1 }));
  }, []);

  const handleFilterChange = useCallback(
    (filters: { gender?: Gender; active?: boolean }) => {
      setSearchParams((prev) => ({
        ...prev,
        ...filters,
        page: 1,
      }));
    },
    [],
  );

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Patients
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {data?.total != null
              ? `${data.total} patient${data.total !== 1 ? 's' : ''} total`
              : 'Loading...'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className="btn-secondary"
            aria-expanded={showFilters}
            aria-controls="patient-filters"
          >
            <FunnelIcon className="h-4 w-4" />
            Filters
          </button>
          <button
            type="button"
            onClick={() => navigate('/patients/new')}
            className="btn-primary"
          >
            <PlusIcon className="h-4 w-4" />
            New Patient
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="card space-y-4">
        <PatientSearch onSearch={handleSearch} />

        {showFilters && (
          <div
            id="patient-filters"
            className="flex flex-wrap gap-4 border-t border-gray-200 pt-4 dark:border-gray-700"
          >
            <div>
              <label
                htmlFor="filter-gender"
                className="block text-xs font-medium text-gray-500 dark:text-gray-400"
              >
                Gender
              </label>
              <select
                id="filter-gender"
                className="input-base mt-1 w-32"
                onChange={(e) =>
                  handleFilterChange({
                    gender: (e.target.value || undefined) as Gender | undefined,
                  })
                }
                defaultValue=""
              >
                <option value="">All</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label
                htmlFor="filter-status"
                className="block text-xs font-medium text-gray-500 dark:text-gray-400"
              >
                Status
              </label>
              <select
                id="filter-status"
                className="input-base mt-1 w-32"
                onChange={(e) =>
                  handleFilterChange({
                    active:
                      e.target.value === '' ? undefined : e.target.value === 'true',
                  })
                }
                defaultValue=""
              >
                <option value="">All</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Data Table */}
      <DataTable
        columns={columns}
        data={data?.data ?? []}
        keyExtractor={(patient) => patient.id}
        isLoading={isLoading}
        sortBy={searchParams.sortBy}
        sortOrder={searchParams.sortOrder}
        onSort={handleSort}
        onRowClick={handleRowClick}
        page={searchParams.page}
        pageSize={searchParams.pageSize}
        total={data?.total}
        onPageChange={handlePageChange}
        emptyMessage="No patients found"
        emptyIcon={<UsersIcon className="h-10 w-10 text-gray-300" />}
      />
    </div>
  );
}
