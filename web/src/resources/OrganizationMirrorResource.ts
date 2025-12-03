import axiosInstance from 'src/libs/axios';

export interface OrganizationMirror {
    external_registry: string;
    external_namespace: string;
    external_registry_username?: string | null;
    external_registry_password?: string | null;
    sync_interval: number;
    repo_filter_type: 'regex' | 'list';
    repo_filter_value?: string | null;
    internal_robot?: string | null;
    is_enabled: boolean;
    sync_status: string;
    sync_message?: string | null;
    last_sync_start?: string | null;
}

export async function getOrganizationMirror(orgName: string) {
  const response = await axiosInstance.get<OrganizationMirror>(`/api/v1/organization/${orgName}/mirror`);
  return response.data;
}

export async function updateOrganizationMirror(orgName: string, config: Partial<OrganizationMirror>) {
  const response = await axiosInstance.post(`/api/v1/organization/${orgName}/mirror`, config);
  return response.data;
}

export async function syncNowOrganizationMirror(orgName: string) {
  const response = await axiosInstance.post(`/api/v1/organization/${orgName}/mirror/sync-now`);
  return response.data;
}

