import { useState } from "react";
import { companiesApi } from "../../api/companies";
import { useCompanyStore } from "../../store/companyStore";
import type { CompanyProfile } from "../../api/types";

export function CompanyPanel() {
  const { profile, setCompany } = useCompanyStore();
  const [showForm, setShowForm] = useState(!profile);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: profile?.name ?? "",
    cpv_codes: profile?.cpv_codes.join(", ") ?? "",
    regions: profile?.regions.join(", ") ?? "",
    annual_turnover: profile?.annual_turnover?.toString() ?? "0",
    capacity_tags: profile?.capacity_tags.join(", ") ?? "",
    exclusion_flags: profile?.exclusion_flags.join(", ") ?? "",
  });

  function split(v: string): string[] {
    return v
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const payload: Partial<CompanyProfile> & { name: string } = {
        name: form.name,
        cpv_codes: split(form.cpv_codes),
        regions: split(form.regions),
        annual_turnover: parseFloat(form.annual_turnover) || 0,
        capacity_tags: split(form.capacity_tags),
        exclusion_flags: split(form.exclusion_flags),
      };
      const saved = await companiesApi.create(payload);
      setCompany(saved);
      setShowForm(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  if (!showForm && profile) {
    return (
      <div className="rounded-lg border border-[#1e2530] bg-[#161a22] p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-[#e8eaed]">{profile.name}</p>
            <p className="mt-0.5 text-xs text-[#8b93a0]">
              {profile.cpv_codes.length} CPV codes · {profile.regions.length} regions
            </p>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="text-xs text-[#c9a84c] hover:text-[#a07c34]"
          >
            Edit
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-[#1e2530] bg-[#161a22] p-4">
      <h3 className="mb-3 text-sm font-semibold text-[#e8eaed]">Company Profile</h3>
      <div className="space-y-2">
        {(
          [
            ["name", "Company name", "text"],
            ["cpv_codes", "CPV codes (comma-separated)", "text"],
            ["regions", "NUTS regions (comma-separated)", "text"],
            ["annual_turnover", "Annual turnover (EUR)", "number"],
            ["capacity_tags", "Capacity tags (comma-separated)", "text"],
          ] as const
        ).map(([field, label]) => (
          <div key={field}>
            <label className="mb-0.5 block text-xs text-[#8b93a0]">{label}</label>
            <input
              type="text"
              value={form[field]}
              onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
              className="w-full rounded-md border border-[#1e2530] bg-[#0f1117] px-3 py-1.5 text-sm text-[#e8eaed] outline-none focus:border-[#c9a84c]/50"
            />
          </div>
        ))}
      </div>
      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
      <div className="mt-3 flex gap-2">
        <button
          onClick={handleSave}
          disabled={saving || !form.name}
          className="rounded-md bg-[#c9a84c] px-4 py-1.5 text-sm font-medium text-[#0f1117] hover:bg-[#a07c34] disabled:opacity-50 transition-colors"
        >
          {saving ? "Saving…" : "Save"}
        </button>
        {profile && (
          <button
            onClick={() => setShowForm(false)}
            className="text-sm text-[#8b93a0] hover:text-[#e8eaed]"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
