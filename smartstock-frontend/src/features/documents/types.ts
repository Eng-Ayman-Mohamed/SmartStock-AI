export type DocType = 'policy' | 'contract' | 'procedure' | 'specification';

export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  doc_type: DocType;
  file_size: number;
  total_chunks: number;
  cloudinary_url: string;
  uploaded_by: number | null;
  uploaded_by_username: string | null;
  ingested_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UploadDocumentPayload {
  file: File;
  doc_type: DocType;
}
