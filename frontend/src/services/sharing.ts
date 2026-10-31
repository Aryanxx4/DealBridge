import { api, downloadFile } from "@/services/api";
import type { FollowUp, SellerAssessmentRow, SellerAssessmentView, SellerOrg, ShareRow } from "@/types/api";

export const sharingApi = {
  sellerOrgs: () => api.get<SellerOrg[]>("/seller-orgs"),
  shares: (id: string) => api.get<ShareRow[]>(`/assessments/${id}/shares`),
  share: (id: string, sellerOrgId: string, versionNo: number | undefined) => api.post<{ share_id: string; stale: boolean }>(`/assessments/${id}/share`, { seller_org_id: sellerOrgId, version_no: versionNo ?? null, confirm: true }),
  unshare: (id: string, sellerOrgId: string) => api.post<{ revoked: number }>(`/assessments/${id}/unshare`, { seller_org_id: sellerOrgId }),
  excel: (id: string, versionNo?: number) => downloadFile(`/assessments/${id}/report.xlsx${versionNo ? `?version=${versionNo}` : ""}`, "DealBridge_Assessment.xlsx"),
  downloadDocument: (docId: string, name: string) => downloadFile(`/documents/${docId}/download`, name),
  uploadSellerDocument: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post<{ id: string; original_filename: string }>("/seller/documents", fd);
  },
  attachToResponse: (responseId: string, ids: string[]) => api.post(`/seller-responses/${responseId}/attachments`, { document_ids: ids }),
  attachToFollowUp: (fid: string, ids: string[]) => api.post<FollowUp>(`/follow-ups/${fid}/attachments`, { document_ids: ids }),
  team: () => api.get<{ id: string; display_name: string }[]>("/seller/team"),
  assignOwner: (fid: string, ownerId: string | null) => api.patch<FollowUp>(`/follow-ups/${fid}/owner`, { owner_user_id: ownerId }),
  report: (id: string, versionNo?: number) => downloadFile(`/assessments/${id}/report.pdf${versionNo ? `?version=${versionNo}` : ""}`, "DealBridge_Assessment.pdf"),
  followUps: (id: string) => api.get<FollowUp[]>(`/assessments/${id}/follow-ups`),
  followUp: (id: string) => api.get<FollowUp>(`/follow-ups/${id}`),
  createFollowUp: (id: string, body: { seller_org_id: string; subject: string; message: string; related_requirement_ids: string[] }) => api.post<FollowUp>(`/assessments/${id}/follow-ups`, body),
  buyerMessage: (fid: string, body: string) => api.post<FollowUp>(`/follow-ups/${fid}/messages`, { body }),
  close: (fid: string) => api.post<FollowUp>(`/follow-ups/${fid}/close`),
  // seller
  sellerAssessments: () => api.get<SellerAssessmentRow[]>("/seller/assessments"),
  sellerAssessment: (id: string, version?: number) => api.get<SellerAssessmentView>(`/seller/assessments/${id}${version ? `?version=${version}` : ""}`),
  sellerFollowUps: (status?: string) => api.get<FollowUp[]>(`/seller/follow-ups${status ? `?status=${status}` : ""}`),
  sellerResponse: (requirementId: string, body: { version_no: number; body: string; assertion: string }) => api.post(`/requirements/${requirementId}/seller-response`, body),
  accept: (fid: string) => api.post<FollowUp>(`/follow-ups/${fid}/accept`),
  reject: (fid: string, reason: string) => api.post<FollowUp>(`/follow-ups/${fid}/reject`, { reason }),
  respond: (fid: string, body: string) => api.post<FollowUp>(`/follow-ups/${fid}/responses`, { body }),
};
