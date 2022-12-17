from .models import Submission, Group, RepSecret, Moderation 
from .models import CONFESSION, COMMENT, REPLY
from .models import PENDING
from .post import fb_post, ig_post, tc_post
from tcx import settings
import threading
import random
import uuid

MOD_REQ = 5 # max moderations users could be asked to perform
# YAY_THRESH = 3 # yays to go from pending to accepted (includes submitter's implicit mod)
# NAY_THRESH = 2 # nays to go from pending to rejected
YN_MIN = 5 # minimum vote value to reach verdict (unanimous case)
YN_MAX = 9 # will reach verdict if approaches this, regardless how close the vote
# MAX_COMS = 5 # maximum comments a confession can have

# json headers *match with constants in submission.html
MOD = 'mod'
SUBMITTED = 'submitted'
REP_STATS = 'rep_stats'
INIT = 'init'
ADMIN = 'admin'
DEV = 'dev'

# add 1 to page counter
def page_count(group):
    grp = Group.objects.get(pk=group)
    grp.visits += 1
    grp.save()

# check user into session
def get_user(req):
    if 'user' in req.session:
        return(req.session['user'])
    req.session['user'] = str(uuid.uuid1())
    return(req.session['user'])

# distinguishes between conf and comments/replies
def get_context(group, parent_num):
    grp = Group.objects.get(pk=group)
    if parent_num == None:
        return({
            'group': group,
            'type': CONFESSION,
            'fb_url': grp.fb_url,
            'ig_url': grp.ig_url,
            'color1': grp.color1,
            'color2': grp.color2,
            'color3': grp.color3,
            'color4': grp.color4
        })
    else:
        parent = Submission.objects.get(group=group, sub_num=parent_num)
        sub_type = ''
        if parent.parent_id == None:
            sub_type = COMMENT
        else:
            sub_type = REPLY
        return({
            'group': group,
            'type': sub_type,
            'parent_num': parent_num,
            'parent_content': parent.content,
            'fb_url': grp.fb_url,
            'ig_url': grp.ig_url,
            'color1': grp.color1,
            'color2': grp.color2,
            'color3': grp.color3,
            'color4': grp.color4
        })

# post to public platform(s)
def publish(sub):
    group = Group.objects.get(pk=sub.group)
    parent = None
    if sub.parent_id != None:
        parent = Submission.objects.get(id=sub.parent_id)
    # non-application specific data
    post_data = {
        'group': sub.group,
        'type': sub.sub_type(),
        'sub_num': sub.sub_num,
        'as_op': parent != None and sub.toggle,
        'cw': sub.get_post_cw(),
        'content': sub.content,
        'dt_sub': sub.short_local_dt(sub.dt_sub),
        'token': group.token
    }
    # post to facebook
    if group.fb_page_id != None:
        parent_fb_id = group.fb_page_id if parent == None else parent.fb_id
        post_data['parent_id'] = parent_fb_id
        sub.fb_id = fb_post(post_data)
        sub.save()
    # post to instagram
    if group.ig_user_id != None:
        parent_ig_id = group.ig_user_id if parent == None else parent.ig_id
        post_data['parent_id'] = parent_ig_id
        post_data['color'] = group.color3
        sub.ig_id = ig_post(post_data)
        sub.save()
    # copy to TC# ---temporary
    if parent == None and sub.toggle:
        tc_post(post_data)

# check if submission ready to be rejected, accepted or remain pending (using gradiated verdict)
def check_verdict(sub):
    nay_lead_prog = (sub.nays - YN_MIN) / (YN_MAX - YN_MIN) # Ex.)           |YN_MIN |nays |YN_MAX -> ~halfway
    yay_lag_prog = sub.yays / YN_MAX                        # Ex.) |0           |yays      |YN_MAX -> ~halfway
    yay_lead_prog = (sub.yays - YN_MIN) / (YN_MAX - YN_MIN) # Same but for case that yays leads
    nay_lag_prog = sub.nays / YN_MAX                        # Also same but for yay lead
    print('yays:', sub.yays, 'nays:', sub.nays, flush=True)

    if sub.yays > sub.nays:
        print('yay_lead_prog:', yay_lead_prog, 'nay_lag_prog:', nay_lag_prog, flush=True)
    else:
        print('nay_lead_prog:', nay_lead_prog, 'yay_lag_prog', yay_lag_prog, flush=True)

    if nay_lead_prog >= yay_lag_prog or sub.nays >= YN_MAX:
        print('rejecting...', flush=True)
        acc_points = 1 - (min(sub.yays, YN_MAX) / YN_MAX)
        sub.reject(acc_points)
    elif yay_lead_prog >= nay_lag_prog or sub.yays >= YN_MAX:
        print('accepting!', flush=True)
        acc_points = 1 - (min(sub.nays, YN_MAX) / YN_MAX)
        sub.accept(acc_points)
        threading.Thread(target=publish, args=[sub]).start() # comment this line to prevent publishing
    else:
        print('still pending....', flush=True)

# submitting moderation
def submit_moderation(mod_data):
    mod = Moderation.create(mod_data)
    # add rep stats
    if len(list(RepSecret.objects.filter(name=mod.rep_secret, group=mod.group))) == 0:
        RepSecret.create(mod.rep_secret, mod.group)
    rep = RepSecret.objects.get(name=mod.rep_secret, group=mod.group)
    rep.mod()
    # update sub's judged stats
    sub = Submission.objects.get(id=mod.sub_id)
    sub.moderate(mod)
    check_verdict(sub)
    # if sub.nays >= NAY_THRESH:
    #     sub.reject()
    # elif sub.yays >= YAY_THRESH:
    #     sub.accept()
    #     print('new post!!!!', flush=True)
    #     publish(sub) # comment this line out to prevent publishing to public platform(s)

# get new pending sub to mod, or None if none exist, and min mods left
def get_sub_to_mod(modded, group):
    if Group.objects.get(pk=group).status != 'GREEN':
        return((None,0))
    subs_pending = list(Submission.objects.filter(group=group, status=PENDING))
    subs_viable = [s for s in subs_pending if s.id not in modded and s.ready()]
    viable_left = len(subs_viable)
    sub_to_mod = None if viable_left == 0 else subs_viable.pop(random.randrange(len(subs_viable)))
    return((sub_to_mod, viable_left))

# send new submission to moderate
def send_to_moderate(mods_left, sub_to_mod):
    print('about to send:', sub_to_mod.content)
    return({
        'header': MOD,
        'mods_left': mods_left,
        'mod_id': sub_to_mod.id,
        'mod_type': sub_to_mod.sub_type(),
        'mod_content': sub_to_mod.content
    })

# submit new submission
def submit_for_review(sub_data):
    # sub_data = { group, parent_num, sub_content, rep_secret, toggle }
    print('submitting content for review now... (saving in database):', sub_data['sub_content'])
    sub = Submission.create(sub_data)
    # make new RepSecret if never used before
    if len(list(RepSecret.objects.filter(group=sub.group, name=sub.rep_secret))) == 0:
        RepSecret.create(sub.rep_secret, sub.group)
    rep = RepSecret.objects.get(group=sub.group, name=sub.rep_secret)
    rep.submit()
    avg_delay = Group.objects.get(pk=sub.group).avg_delay
    # submit implicit moderation by self
    mod_data = {
        'group': sub.group,
        'rep_secret': sub.rep_secret,
        'sub_id': sub.id, # moderation of self
        'yay': True,
        'quality': 0, # placeholder
        'cw': {}
    }
    submit_moderation(mod_data)
    return({'header': SUBMITTED, 'avg_delay': avg_delay})

# sends rep_stats
def check_rep_stats(data):
    # data = { header : string, rep_secret : string, parent_num : string/None, group : string }
    reps = list(RepSecret.objects.filter(group=data['group'], name=data['rep_secret']))
    if len(reps) != 1:
        return({'header': REP_STATS}) # rep-secret DNE
    rep = reps[0]
    as_op = False
    if data['parent_num'] != None:
        parent = Submission.objects.get(group=data['group'], sub_num=data['parent_num'])
        as_op = parent.rep_secret == data['rep_secret']
    return({
        'header': REP_STATS,
        'last_used': rep.last_used,
        'rep_score': rep.rep_score,
        't1_err': rep.t1_error(),
        't2_err': rep.t2_error(),
        'subs_list': rep.subs_list(),
        'percentiles': rep.percentiles(), # (t1_error, t2_error, rep-score)
        'op_reply': as_op
    })

# sends mod if available, or sends to review
def presubmit(data):
    # data = { header, parent_num, sub_content, rep_secret, modded, toggle, [yay, quality, cw], group }
    modded = data['modded']
    sub_data = {
        'group': data['group'],
        'parent_num': data['parent_num'],
        'sub_content': data['sub_content'],
        'rep_secret': data['rep_secret'],
        'toggle': data['toggle']
    }
    # moderate if necessary
    if len(modded) > 0:
        mod_data = {
            'group': data['group'],
            'rep_secret': data['rep_secret'],
            'sub_id': modded[-1], # last added to list is next to be modded,
            'yay': data['yay'],
            'quality': data['quality'],
            'cw': data['cw']
        }
        submit_moderation(mod_data)
    # get next sub to mod or None
    sub_to_mod, viable_left = get_sub_to_mod(modded, data['group'])
    # check if more to moderate, or ready to submit
    mods_left = min(MOD_REQ - len(modded), viable_left)
    if mods_left > 0 and sub_to_mod != None:
        return send_to_moderate(mods_left, sub_to_mod)
    else:
        return submit_for_review(sub_data)

# get all pending posts & anything else to be seen on dev dashboard
def dev_info(code):
    if code != settings.DEV_PSWD['dash']:
        return({'header': 'fail'})
    subs_pending = []
    for s in Submission.objects.all():
        if s.status == PENDING:
            subs_pending.append(s.rep_stats())
    info = {
        'header': DEV,
        'pending': subs_pending
    }
    return(info)

# dev push through submission to acceptance
def dev_accept(sub_id):
    sub = Submission.objects.get(id=sub_id)
    sub.dev_accept(YN_MAX)
    check_verdict(sub)
    return({'header': 'accepted'})

def dev_post(group, content):
    # post_info = { type, sub_num, as_op, cw, content, dt_sub, parent_id }
    grp = Group.objects.get(pk=group)
    post_info = {
        'type': CONFESSION,
        'sub_num': 'Announcement',
        'as_op': False,
        'cw': '',
        'content': content,
        'dt_sub': '',
        'parent_id': grp.ig_user_id,
        'color': grp.color3,
        'group': group,
        'token': grp.token
    }
    ig_id = ig_post(post_info)
    return({'header': 'accepted'})

def handle_dev(data):
    header = data['header']
    if header == 'code':
        return dev_info(data['code'])
    elif header == 'accept':
        return dev_accept(data['sub_id'])
    elif header == 'dev_post':
        return dev_post(data['group'], data['content'])


# handles all possible traces upon receiving a POST
def handle_post(data, group):
    header = data['header']
    data['group'] = group

    if header == REP_STATS:
        return(check_rep_stats(data))
    if header == INIT or MOD:
        ############## DEBUGGING ##################
        if admin_check(data['sub_content']):
            return({'header': ADMIN})
        ###########################################
        return(presubmit(data))
    print('unknown header')
    return({})

#########################################

# admin database commands. Probably just for debugging / testing
def admin_check(content):
    if content == settings.DEV_PSWD['clean']:
        print('deleting subs, mods, & reps...')
        Submission.objects.all().delete()
        Moderation.objects.all().delete()
        RepSecret.objects.all().delete()
        for g in Group.objects.all():
            g.next_num = 1
            g.num_posts = 0
            g.avg_delay = 0
            g.visits = 0
            g.save()
        return(True)
    elif content == settings.DEV_PSWD['reset']:
        print('deleting subs, mods, reps & groups...')
        Submission.objects.all().delete()
        Moderation.objects.all().delete()
        RepSecret.objects.all().delete()
        Group.objects.all().delete()
        # # Group 1
        # group1 = Group(
        #     name = 'Test1',
        #     color1 = '#f58025',
        #     color2 = '#000000',
        #     color3 = '#e77500',
        #     color4 = '#fff1dc',
        #     timezone = 'ET',
        #     fb_page_id = '109774098197021',
        #     fb_url = 'https://www.facebook.com/Test-Page-Name-109774098197021',
        #     ig_user_id = '17841450357747490',
        #     ig_url = 'https://www.instagram.com/tygerz1746/'
        # )
        # group1.save()
        # # Group 2
        # group2 = Group(
        #     name = 'Test2',
        #     timezone = 'PT',
        #     fb_page_id = '638900900472723' # actually group id
        # )
        # group2.save()
        return(True)

    ######## Runtime Master Commands #######
    elif content == settings.DEV_PSWD['green'] or content == settings.DEV_PSWD['GREEN']:
        print('making all groups live...')
        for g in Group.objects.all():
            g.status = 'GREEN'
            g.save()
        return(True)
    elif content == settings.DEV_PSWD['yellow'] or content == settings.DEV_PSWD['YELLOW']:
        print('pausing posting for all groups...')
        for g in Group.objects.all():
            g.status = 'YELLOW'
            g.save()
        return(True)
    elif content == settings.DEV_PSWD['red'] or content == settings.DEV_PSWD['RED']:
        print('pausing submissions for all groups...')
        for g in Group.objects.all():
            g.status = 'RED'
            g.save()
        return(True)

    return(False)

    
