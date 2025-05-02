from django.views.generic import TemplateView

class IndexView(TemplateView):
    template_name = 'index.html'

def page_not_found_view(request, exception):
    return TemplateView.as_view(template_name='404.html')(request)