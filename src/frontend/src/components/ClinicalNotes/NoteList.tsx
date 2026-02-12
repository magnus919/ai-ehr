import { useClinicalNotes } from '@/hooks/useClinicalNotes';
import { formatDate } from '@/utils/formatters';

interface NoteListProps {
  patientId: string;
  onSelectNote?: (noteId: string) => void;
}

const NOTE_TYPE_LABELS: Record<string, string> = {
  progress: 'Progress',
  soap: 'SOAP',
  h_and_p: 'H&P',
  discharge: 'Discharge',
  procedure: 'Procedure',
  consultation: 'Consultation',
};

function getStatusBadge(status: string, signedAt?: string) {
  if (signedAt) {
    return (
      <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-950 dark:text-green-300">
        Signed
      </span>
    );
  }

  const styles: Record<string, string> = {
    'in-progress': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300',
    completed: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
    draft: 'bg-gray-100 text-gray-800 dark:bg-gray-950 dark:text-gray-300',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
        styles[status] || styles.draft
      }`}
    >
      {status === 'in-progress' ? 'In Progress' : status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

export function NoteList({ patientId, onSelectNote }: NoteListProps) {
  const { data: notes, isLoading } = useClinicalNotes({ patient_id: patientId });

  if (isLoading) {
    return (
      <div className="card">
        <p className="text-gray-500">Loading clinical notes...</p>
      </div>
    );
  }

  if (!notes || notes.length === 0) {
    return (
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Clinical Notes
        </h2>
        <p className="mt-4 text-gray-500">No clinical notes found.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
        Clinical Notes
      </h2>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Type
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Author
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
            {notes.map((note) => (
              <tr
                key={note.id}
                className="hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                  {formatDate(note.created_at)}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                  {NOTE_TYPE_LABELS[note.note_type] || note.note_type}
                </td>
                <td className="px-4 py-3">
                  {getStatusBadge(note.status, note.signed_at)}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                  {note.author_id}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => onSelectNote?.(note.id)}
                    className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
