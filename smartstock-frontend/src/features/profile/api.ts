import api from '../../lib/axios';

export interface UpdateProfileData {
  name?: string;
  email?: string;
}

export async function updateProfile(data: UpdateProfileData): Promise<void> {
  await api.patch('/auth/me/', data);
}
