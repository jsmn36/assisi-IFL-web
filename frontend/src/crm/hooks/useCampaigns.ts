import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { crmCampaignsApi } from '../api/crmClient';
import type { CampaignCreate } from '../types/crm';

export function useCampaigns() {
  return useQuery({ 
    queryKey: ['crm', 'campaigns'], 
    queryFn: crmCampaignsApi.list, 
    staleTime: 60_000 
  });
}

export function useCreateCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CampaignCreate) => crmCampaignsApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['crm', 'campaigns'] }),
  });
}

export function useSendCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => crmCampaignsApi.send(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['crm', 'campaigns'] }),
  });
}
