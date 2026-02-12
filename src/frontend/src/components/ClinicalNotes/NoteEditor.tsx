import { useState, useEffect } from 'react';
import { useCreateClinicalNote, useUpdateClinicalNote, useSignClinicalNote } from '@/hooks/useClinicalNotes';
import type { ClinicalNote } from '@/services/clinicalNotes';

interface NoteEditorProps {
  patientId: string;
  encounterId?: string;
  note?: ClinicalNote;
  onSuccess?: () => void;
}

const NOTE_TYPES = [
  { value: 'progress', label: 'Progress Note' },
  { value: 'soap', label: 'SOAP Note' },
  { value: 'h_and_p', label: 'History & Physical' },
  { value: 'discharge', label: 'Discharge Summary' },
  { value: 'procedure', label: 'Procedure Note' },
  { value: 'consultation', label: 'Consultation' },
];

export function NoteEditor({ patientId, encounterId, note, onSuccess }: NoteEditorProps) {
  const [noteType, setNoteType] = useState(note?.note_type || 'soap');
  const [subjective, setSubjective] = useState('');
  const [objective, setObjective] = useState('');
  const [assessment, setAssessment] = useState('');
  const [plan, setPlan] = useState('');
  const [isPsychotherapyNote, setIsPsychotherapyNote] = useState(note?.is_psychotherapy_note || false);
  const [is42CFRPart2, setIs42CFRPart2] = useState(note?.is_42cfr_part2 || false);

  const createNote = useCreateClinicalNote();
  const updateNote = useUpdateClinicalNote();
  const signNote = useSignClinicalNote();

  useEffect(() => {
    if (note) {
      setNoteType(note.note_type);
      setIsPsychotherapyNote(note.is_psychotherapy_note);
      setIs42CFRPart2(note.is_42cfr_part2);
    }
  }, [note]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();

    const content = JSON.stringify({
      subjective,
      objective,
      assessment,
      plan,
    });

    if (note) {
      await updateNote.mutateAsync({
        id: note.id,
        input: { content },
      });
    } else {
      await createNote.mutateAsync({
        patient_id: patientId,
        encounter_id: encounterId,
        note_type: noteType,
        content,
        is_psychotherapy_note: isPsychotherapyNote,
        is_42cfr_part2: is42CFRPart2,
      });
    }

    if (onSuccess) onSuccess();
  };

  const handleSign = async () => {
    if (note) {
      await signNote.mutateAsync(note.id);
      if (onSuccess) onSuccess();
    }
  };

  const isSigned = note?.signed_at != null;
  const isDisabled = isSigned || createNote.isPending || updateNote.isPending;

  return (
    <form onSubmit={handleSave} className="card space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          {note ? 'Edit Clinical Note' : 'New Clinical Note'}
        </h2>
        {isSigned && (
          <span className="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-950 dark:text-green-300">
            Signed
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Note Type
          </label>
          <select
            value={noteType}
            onChange={(e) => setNoteType(e.target.value)}
            disabled={isDisabled}
            className="input-base mt-1"
          >
            {NOTE_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={isPsychotherapyNote}
              onChange={(e) => setIsPsychotherapyNote(e.target.checked)}
              disabled={isDisabled}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              Psychotherapy Note
            </span>
          </label>
          {isPsychotherapyNote && (
            <p className="text-xs text-yellow-600 dark:text-yellow-400">
              Special protections apply under HIPAA
            </p>
          )}

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={is42CFRPart2}
              onChange={(e) => setIs42CFRPart2(e.target.checked)}
              disabled={isDisabled}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              42 CFR Part 2 Protected
            </span>
          </label>
        </div>
      </div>

      {noteType === 'soap' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Subjective
            </label>
            <textarea
              value={subjective}
              onChange={(e) => setSubjective(e.target.value)}
              disabled={isDisabled}
              rows={4}
              placeholder="Patient's complaints, symptoms, and history..."
              className="input-base mt-1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Objective
            </label>
            <textarea
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              disabled={isDisabled}
              rows={4}
              placeholder="Physical exam findings, vital signs, lab results..."
              className="input-base mt-1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Assessment
            </label>
            <textarea
              value={assessment}
              onChange={(e) => setAssessment(e.target.value)}
              disabled={isDisabled}
              rows={4}
              placeholder="Diagnosis, clinical impression..."
              className="input-base mt-1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Plan
            </label>
            <textarea
              value={plan}
              onChange={(e) => setPlan(e.target.value)}
              disabled={isDisabled}
              rows={4}
              placeholder="Treatment plan, medications, follow-up..."
              className="input-base mt-1"
            />
          </div>
        </div>
      )}

      <div className="flex justify-end gap-2">
        {!isSigned && (
          <>
            <button
              type="submit"
              className="btn-secondary"
              disabled={isDisabled}
            >
              {createNote.isPending || updateNote.isPending ? 'Saving...' : 'Save Draft'}
            </button>
            {note && (
              <button
                type="button"
                onClick={handleSign}
                className="btn-primary"
                disabled={signNote.isPending}
              >
                {signNote.isPending ? 'Signing...' : 'Sign Note'}
              </button>
            )}
          </>
        )}
      </div>
    </form>
  );
}
