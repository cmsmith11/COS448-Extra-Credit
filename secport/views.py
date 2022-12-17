from .backend import handle_post, get_user, get_context, handle_dev, page_count
from .models import Submission, Group
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.http import Http404
from django.http import JsonResponse
import json

# main landing page
def index(request):
    return render(request, 'secport/index.html')

def prelinks(request, group):
    get_object_or_404(Group, pk=group) # verify group is valid
    context = get_context(group, None)
    return render(request, 'secport/prelinks.html', context)

# specify conf_num when commenting
def submission(request, group, parent_num=None):
    print('this is server-side code... parent_num:', parent_num, flush=True)

    # validations
    get_object_or_404(Group, pk=group) # verify group is valid
    page_count(group)
    if Group.objects.get(pk=group).status == 'RED':
        raise Http404("This group is in status RED")
    if parent_num != None:
        print('checking parent_num!:', parent_num, flush=True)
        get_object_or_404(Submission, group=group, sub_num=parent_num) # check parent is valid

    # handle submission, moderation or other random things
    if request.method == 'POST':
        from_client = json.loads(request.body)
        to_client = handle_post(from_client, group)
        return JsonResponse(to_client)

    # page loading, and anything else besides POSTs
    user = get_user(request)
    print('user:', user)

    context = get_context(group, parent_num)
    return render(request, 'secport/submission.html', context)

# dev control center
def dashboard(request):
    if request.method == 'POST':
        from_client = json.loads(request.body)
        return JsonResponse(handle_dev(from_client))
    return render(request, 'secport/dashboard.html')

# FB policy or whatever
def privacy(request):
    return HttpResponse("Privacy Policy: We do not collect any data that you do not willfully give us, and we only use data for purposes necessary to the core functionality of this application.")
