from django.db import models

# Create your models here.
class GitRepository(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()

    def __str__(self):
        return self.name
    
class GitBranch(models.Model):
    repository = models.ForeignKey(GitRepository, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    
class GitCommit(models.Model):
    repository = models.ForeignKey(GitRepository, on_delete=models.CASCADE, related_name='commits')
    commit_hash = models.CharField(max_length=40)
    author = models.CharField(max_length=255)
    message = models.TextField()
    date = models.DateTimeField()

    def __str__(self):
        return f"{self.commit_hash} - {self.author}"
    
class GithubUser(models.Model):
    name = models.CharField(max_length=255)
    