"""
sentry.web.frontend.projects.settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.contrib import messages
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import ugettext_lazy as _

from sentry.constants import MEMBER_OWNER
from sentry.models import Team
from sentry.permissions import can_remove_project
from sentry.plugins import plugins
from sentry.web.decorators import has_access
from sentry.web.forms.projects import EditProjectForm
from sentry.web.helpers import render_to_response


@has_access(MEMBER_OWNER)
@csrf_protect
def manage_project(request, team, project):
    result = plugins.first('has_perm', request.user, 'edit_project', project)
    if result is False and not request.user.is_superuser:
        return HttpResponseRedirect(reverse('sentry'))

    team_list = Team.objects.get_for_user(project.owner or request.user, MEMBER_OWNER)

    form = EditProjectForm(request, team_list, request.POST or None, instance=project, initial={
        'origins': '\n'.join(project.get_option('sentry:origins', None) or []),
        'owner': project.owner,
        'resolve_age': int(project.get_option('sentry:resolve_age', 0)),
        'mail_subject_prefix': project.get_option('mail:subject_prefix', settings.EMAIL_SUBJECT_PREFIX),
    })

    if form.is_valid():
        project = form.save()
        project.update_option('sentry:origins', form.cleaned_data.get('origins') or [])
        project.update_option('sentry:resolve_age', form.cleaned_data.get('resolve_age'))
        project.update_option('mail:subject_prefix', form.cleaned_data.get('mail_subject_prefix'))
        messages.add_message(
            request, messages.SUCCESS,
            _('Changes to your project were saved.'))

        return HttpResponseRedirect(reverse('sentry-manage-project', args=[team.slug, project.slug]))

    context = csrf(request)
    context.update({
        'team': team,
        'can_remove_project': can_remove_project(request.user, project),
        'page': 'details',
        'form': form,
        'project': project,
    })

    return render_to_response('sentry/projects/manage.html', context, request)
