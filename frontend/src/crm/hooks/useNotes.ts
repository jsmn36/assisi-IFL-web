import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { crmNotesApi } from '../api/crmClient';
import type { NoteCreate } from '../types/crm';

export function useNotes(guestId: number) {
  return useQuery({
    queryKey: ['crm', 'guest', guestId, 'notes'],
    queryFn: () => crmNotesApi.list(guestId),
    staleTime: 30_000,
    enabled: guestId > 0,
  });
}

export function useAddNote(guestId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: NoteCreate) => crmNotesApi.create(guestId, payload),
    onSuccess: () => {
      // Invalidate both the detail query and the notes query
      qc.invalidateQueries({ queryKey: ['crm', 'guest', guestId] });
      qc.invalidateQueries({ queryKey: ['crm', 'guest', guestId, 'notes'] });
    },
  });
}
