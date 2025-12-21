import { ProjectsTable } from '@/components/projects-table';
import { getProjects, getKPIs } from '@/lib/data';

export const revalidate = 60;

export default async function ProjectsPage() {
  const [projects, kpis] = await Promise.all([
    getProjects(),
    getKPIs(),
  ]);

  // Enrich projects with KPI data
  const projectsWithKPIs = projects.map(project => {
    const budget = kpis.find(
      k => k.metric_name === 'budget' && k.dimension === 'project' && k.dimension_value === project.project_id
    )?.value || 0;
    const actual = kpis.find(
      k => k.metric_name === 'actual' && k.dimension === 'project' && k.dimension_value === project.project_id
    )?.value || 0;
    const burnRate = kpis.find(
      k => k.metric_name === 'burn_rate' && k.dimension === 'project' && k.dimension_value === project.project_id
    )?.value || 0;

    return {
      ...project,
      budget,
      actual,
      variance: actual - budget,
      burnRate,
    };
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
        <p className="text-muted-foreground">
          Browse and analyze project portfolio
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Total Projects</p>
          <p className="text-2xl font-bold">{projects.length}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Active</p>
          <p className="text-2xl font-bold text-green-600">
            {projects.filter(p => p.status === 'active').length}
          </p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">At Risk</p>
          <p className="text-2xl font-bold text-yellow-600">
            {projectsWithKPIs.filter(p => p.burnRate > 100).length}
          </p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Completed</p>
          <p className="text-2xl font-bold text-blue-600">
            {projects.filter(p => p.status === 'completed').length}
          </p>
        </div>
      </div>

      {/* Projects Table */}
      <div className="rounded-lg border bg-card">
        <ProjectsTable projects={projectsWithKPIs} />
      </div>
    </div>
  );
}
