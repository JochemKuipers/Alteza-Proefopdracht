from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class IndexView(TemplateView):
    template_name = 'index.html'


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'account/profile.html'