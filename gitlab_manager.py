import gitlab

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

    def get_job_trace(self, project_id, job_id):
        project = self.get_project(project_id)
        job = project.jobs.get(job_id)
        trace = job.trace()
        # Decode bytes to string if necessary
        if isinstance(trace, bytes):
            return trace.decode('utf-8', errors='replace')
        return trace

