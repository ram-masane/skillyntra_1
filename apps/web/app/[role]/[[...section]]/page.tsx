import AppShell from "../../../components/app-shell";

export default async function RolePage({ params }: { params: Promise<{ role: string; section?: string[] }> }) {
  const resolved = await params;
  return <AppShell role={resolved.role} section={resolved.section?.join("/")} />;
}
