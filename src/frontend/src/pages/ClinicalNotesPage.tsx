import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { NoteEditor } from '@/components/ClinicalNotes/NoteEditor';
import { NoteList } from '@/components/ClinicalNotes/NoteList';
import { useClinicalNote } from '@/hooks/useClinicalNotes';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { useUIStore } from '@/store/uiStore';

export default function ClinicalNotesPage() {
  const [searchParams] = useSearchParams();
  const [selectedPatientId, setSelectedPatientId] = useState<string>(
    searchParams.get('patientId') || ''
  );
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null);
  const [showEditor, setShowEditor] = useState(false);

  const { data: selectedNote } = useClinicalNote(selectedNoteId || undefined);
  const setBreadcrumbs = useUIStore((s) => s.setBreadcrumbs);

  useEffect(() => {
    setBreadcrumbs([{ label: 'Clinical Notes' }]);
    return () => setBreadcrumbs([]);
  }, [setBreadcrumbs]);

  const handleSelectNote = (noteId: string) => {
    setSelectedNoteId(noteId);
    setShowEditor(true);
  };

  const handleNewNote = () => {
    setSelectedNoteId(null);
    setShowEditor(true);
  };

  const handleSuccess = () => {
    setShowEditor(false);
    setSelectedNoteId(null);
  };

  return (
    <ErrorBoundary section="Clinical Notes">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Clinical Notes
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Create and manage clinical documentation
            </p>
          </div>
          {selectedPatientId && !showEditor && (
            <button onClick={handleNewNote} className="btn-primary">
              New Note
            </button>
          )}
        </div>

        {!selectedPatientId && (
          <div className="card">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Select Patient
            </label>
            <input
              type="text"
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              placeholder="Enter patient ID"
              className="input-base mt-1"
            />
          </div>
        )}

        {selectedPatientId && (
          <>
            {showEditor && (
              <NoteEditor
                patientId={selectedPatientId}
                note={selectedNote}
                onSuccess={handleSuccess}
              />
            )}
            <NoteList patientId={selectedPatientId} onSelectNote={handleSelectNote} />
          </>
        )}
      </div>
    </ErrorBoundary>
  );
}
