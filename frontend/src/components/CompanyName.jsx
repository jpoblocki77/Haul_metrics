import { useCompany } from "@/context/CompanyContext";
export const CompanyName = ({ testId, className = "" }) => {
  const { company } = useCompany();
  return <span data-testid={testId} className={`company-name break-words ${className}`}>{company.company_name}</span>;
};