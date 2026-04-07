from django.contrib.auth.models import AbstractUser
from django.db import models

class GitRepository(models.Model):
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    url = models.URLField()

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.pk is None:
            self.save()
    
    def get_branches(self):
        return GitBranch.objects.filter(repository=self)
    
    def get_commits(self, branch_name=None):
        commits = GitCommit.objects.filter(repository=self)
        if branch_name:
            commits = commits.filter(branch__name=branch_name)
        
        if not commits.exists():
            from alteza_proefopdracht.apps.gitcommits import github

            if branch_name:
                github.get_branch_commits(self.full_name, branch_name)
            else:
                first_branch = self.get_branches().first()
                if first_branch is not None:
                    github.get_branch_commits(self.full_name, first_branch.name)

            commits = GitCommit.objects.filter(repository=self)
            if branch_name:
                commits = commits.filter(branch__name=branch_name)

        return commits

class GitBranch(models.Model):
    repository = models.ForeignKey(GitRepository, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    
class GitCommit(models.Model):
    repository = models.ForeignKey(GitRepository, on_delete=models.CASCADE, related_name='commits')
    branch = models.ForeignKey(GitBranch, on_delete=models.CASCADE, related_name='commits')
    commit_hash = models.CharField(max_length=40)
    author = models.CharField(max_length=255)
    message = models.TextField()
    date = models.DateTimeField()

    def __str__(self):
        return f"{self.commit_hash} - {self.author}"

class GitUser(AbstractUser):
    def get_repositories(self):
        repositories = GitRepository.objects.filter(commits__author=self.username).distinct()
        if not repositories.exists():
            from alteza_proefopdracht.apps.gitcommits import github
            github.get_user_repositories()
            repositories = GitRepository.objects.filter(commits__author=self.username).distinct()
        return repositories