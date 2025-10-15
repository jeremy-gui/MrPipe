import gitlab
import time
from requests.exceptions import RequestException

class GitLabManager:
    def __init__(self, url, token):
        self.gl = gitlab.Gitlab(url, private_token=token)
        self.gl.auth()

    def get_project(self, project_id):
        return self.gl.projects.get(project_id)

    def get_latest_pipeline(self, project_id):
        project = self.get_project(project_id)
        pipelines = project.pipelines.list(per_page=1, get_all=False)
        return pipelines

    def get_pipeline_jobs(self, project_id, pipeline_id):
        project = self.get_project(project_id)
        pipeline = project.pipelines.get(pipeline_id)
        return pipeline.jobs.list(all=True)

    def get_all_projects(self):
        return self.gl.projects.list(membership=True, get_all=True)

    # Dans gitlab_manager.py
    def get_job_trace(self, project_id, job_id, max_retries=3):
        """Récupère les logs d'un job avec gestion des erreurs et des réessais"""
        for attempt in range(max_retries):
            try:
                project = self.get_project(project_id)
                # Remove lazy=True to ensure we get the full job data
                job = project.jobs.get(job_id)
                
                # Force fetch the trace
                trace = job.trace()
                if trace is not None:
                    return trace
                return ""  # Return empty string if no trace is available

            except gitlab.exceptions.GitlabGetError as e:
                if attempt == max_retries - 1:  # Dernière tentative
                    print(f"Erreur lors de la récupération des logs: {e}")
                    return f"Erreur lors de la récupération des logs: {e}"
                time.sleep(1)  # Attendre avant de réessayer

            except Exception as e:
                print(f"Erreur inattendue: {e}")
                return f"Erreur inattendue lors de la récupération des logs: {e}"

        return "Impossible de récupérer les logs après plusieurs tentatives"