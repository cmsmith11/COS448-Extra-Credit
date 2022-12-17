from django.db import models
from datetime import datetime, timezone, timedelta
import uuid
import json

# statuses
PENDING = 'pending'
REJECTED = 'rejected'
ACCEPTED = 'accepted'
POSTED = 'posted'

# types. Matched with constants in submission.html
CONFESSION = 'confession'
COMMENT = 'comment'
REPLY = 'reply'

# min time between moderating any given submission
MOD_WAIT_MINUTES = 6

# threshhold for adding a content warning. Fraction out of all voting points
CW_THRESH = 0.3

# content warnings *matches with html in submission.html*
SELF_HARM = 'cw1'
VIOLENCE = 'cw2'
SUBST_ABUSE = 'cw3'
NSFW = 'cw4'
SPOILER = 'cw5'
OTHER = 'cw6'

def to_local_time(utc_dt, tz):
    if tz == 'ET':
        return(utc_dt - timedelta(hours=5)) # changes from 4 - 5
    if tz == 'PT':
        return(utc_dt - timedelta(hours=8)) # changes from 7 - 8
    print('Timezone unknown. Using UTC', flush=True)
    return(utc_dt)

def short_time(dt):
    hour = dt.hour % 12 if dt.hour % 12 != 0 else 12
    return(str(hour) + ':' + dt.strftime("%M") + dt.strftime("%p").lower())

def short_date(dt):
    return(str(dt.month) + '/' + str(dt.day) + '/' + dt.strftime("%y"))

def short_dt(dt):
    return(short_date(dt) + ', ' + short_time(dt))

def nice_cw(db_cw):
    if db_cw == SELF_HARM:
        return('self harm')
    if db_cw == VIOLENCE:
        return('violence')
    if db_cw == SUBST_ABUSE:
        return('substance abuse')
    if db_cw == NSFW:
        return('NSFW')
    if db_cw == SPOILER:
        return('spoiler')
    if db_cw == OTHER:
        return('other')

# Stores all relevant data for all submissions (confessions, comments and replies)
class Submission(models.Model):
    # general metadata
    id = models.CharField(primary_key=True, max_length=50)
    fb_id = models.CharField(max_length=40, null=True, blank=True)
    ig_id = models.CharField(max_length=40, null=True, blank=True)
    parent_id = models.CharField(max_length=50, null=True, blank=True)
    #saga = models.CharField(max_length=20, null=True, blank=True) # if head, csv & includes self
    group = models.CharField(max_length=20)
    # data
    content = models.CharField(max_length=10000, null=True, blank=True)
    rep_secret = models.CharField(max_length=30, null=True, blank=True)
    toggle = models.BooleanField(default=False)
    # judgement stats
    yays = models.FloatField(default=0.0)
    nays = models.FloatField(default=0.0)
    quality = models.FloatField(default=0.0)
    cw = models.CharField(max_length=100, default='{}')
    # more meta data
    status = models.CharField(max_length=20, default=PENDING)
    sub_num = models.CharField(max_length=20, default='N/A')
    num_coms = models.IntegerField(default=0)
    dt_sub = models.DateTimeField('when submitted', null=True, blank=True)
    dt_last_mod = models.DateTimeField('when last modded', null=True, blank=True)
    dt_decided = models.DateTimeField('when fully voted', null=True, blank=True)
    dt_published = models.DateTimeField('when published', null=True, blank=True)
    # constructor
    @classmethod
    def create(cls, sub_data):
        print('sub_data:', sub_data, flush=True)
        sub = cls(
            id = str(uuid.uuid1()),
            group = sub_data['group'],
            parent_id = None if sub_data['parent_num'] == None else Submission.objects.get(group=sub_data['group'], sub_num=sub_data['parent_num']).id,
            content = sub_data['sub_content'],
            rep_secret = sub_data['rep_secret'],
            toggle = sub_data['toggle'],
            dt_sub = datetime.now(timezone.utc)
        )
        sub.save()
        return(sub)
    # to string
    def __str__(self):
        return('('+str(self.id)+', '+self.content+')')
    # replacing 'type' field
    def sub_type(self):
        if self.parent_id == None:
            return CONFESSION
        elif Submission.objects.get(id=self.parent_id).parent_id == None:
            return COMMENT
        else:
            return REPLY
    # has been appropriate time since last moderation to be moderated again
    def ready(self):
        if self.dt_last_mod == None:
            return(True)
        print('time since last:', datetime.now(timezone.utc) - self.dt_last_mod, flush=True)
        return(datetime.now(timezone.utc) - self.dt_last_mod > timedelta(minutes=MOD_WAIT_MINUTES))
    # return shortened local date/time
    def short_local_dt(self, utc_dt):
        tz = Group.objects.get(pk=self.group).timezone
        dt = to_local_time(utc_dt, tz)
        return(short_dt(dt))
    # convert from string to dict
    def get_cw(self):
        return(json.loads(self.cw))
    # for when post is finalized
    def get_post_cw(self):
        cw_dict = self.get_cw()
        cw_str = ''
        print('cw_dict:', cw_dict, flush=True)
        for k in cw_dict.keys():
            if cw_dict[k] >= CW_THRESH:
                cw_str += nice_cw(k) + ', '
        if len(cw_str) > 0:
            cw_str = cw_str[:-2]
        print('cw_str:', cw_str, flush=True)
        return(cw_str)
    # convert from dict to string
    def set_cw(self, new_cws, inc):
        cw_dict = self.get_cw()
        for k in new_cws.keys():
            if new_cws[k]:
                if k not in cw_dict:
                    cw_dict[k] = 0
                cw_dict[k] += round(inc * 100) / 100 # round to 2 decimal places
        self.cw = json.dumps(cw_dict)
        self.save()
    # useful for rep-stats
    def rep_stats(self):
        parent_num = None
        if self.parent_id != None:
            parent_num = Submission.objects.get(id=self.parent_id).sub_num
        return({
            'id': self.id,
            'group': self.group,
            'type': self.sub_type(),
            'content': self.content,
            'yays': self.yays,
            'nays': self.nays,
            'status': self.status,
            'sub_num': self.sub_num,
            'parent_num': parent_num,
            'dt_sub': self.dt_sub,
            'dt_decided': self.dt_decided
        })
    # moderate
    def moderate(self, mod):
        rep = RepSecret.objects.get(name=mod.rep_secret, group=mod.group)
        if mod.yay:
            self.yays += rep.rep_score
        else:
            self.nays += rep.rep_score
        self.quality += mod.quality
        self.set_cw(mod.get_cw(), rep.rep_score)
        self.dt_last_mod = datetime.now(timezone.utc)
        self.save()
    # has been fully voted to be rejected
    def reject(self, acc_points):
        self.status = REJECTED
        self.dt_decided = datetime.now(timezone.utc)
        self.save()
        mods = list(Moderation.objects.filter(sub_id=self.id))
        for m in mods:
            rep = RepSecret.objects.get(name=m.rep_secret, group=self.group)
            if m.yay:
                rep.inacc_yays += acc_points
            else:
                rep.acc_nays += acc_points
            rep.save()
            rep.calc_score()
            # can delete m from Moderation table now

    # has been fully voted to be accepted
    def accept(self, acc_points):
        self.status = ACCEPTED
        self.dt_decided = datetime.now(timezone.utc)
        delay = datetime.now(timezone.utc) - self.dt_sub
        group = Group.objects.get(pk=self.group)
        group.add_post(delay.total_seconds())
        if self.sub_type() == CONFESSION:
            self.sub_num = group.inc_num()
        else:
            parent = Submission.objects.get(id=self.parent_id)
            self.sub_num = parent.sub_num + '.' + str(parent.num_coms + 1)
            parent.num_coms += 1
            parent.save()
        self.save()
        mods = list(Moderation.objects.filter(sub_id=self.id))
        for m in mods:
            rep = RepSecret.objects.get(name=m.rep_secret, group=self.group)
            if m.yay:
                rep.acc_yays += acc_points
            else:
                rep.inacc_nays += acc_points
            rep.save()
            rep.calc_score()
            # can delete m from Moderation table now

    def post_info(self):
        return({
            'group': self.group,
            'type': self.type,
            'content': self.content,
            'cw': self.cw,
            'conf_num': self.conf_num,
            'num_coms': self.cw,
            'dt_sub': self.dt_sub
        })

    def dev_accept(self, new_yays):
        self.yays = new_yays
        self.save()

# Represents a single moderation
class Moderation(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    group = models.CharField(max_length=20)
    rep_secret = models.CharField(max_length=20)
    sub_id = models.CharField(max_length=50)
    yay = models.BooleanField(null=True, blank=True)
    quality = models.FloatField(default=0.0)
    cw = models.CharField(max_length=100, null=True, blank=True)
    # constructor
    @classmethod
    def create(cls, mod_data):
        mod = cls(
            id = str(uuid.uuid1()),
            group = mod_data['group'],
            rep_secret = mod_data['rep_secret'],
            sub_id = mod_data['sub_id'],
            yay = mod_data['yay'],
            quality = mod_data['quality'],
            cw = json.dumps(mod_data['cw'])
        )
        mod.save()
        return(mod)
    # to string
    def __str__(self):
        return('('+self.id+', '+str(self.yay)+', '+self.rep_secret+')')
    # turn db string to dict
    def get_cw(self):
        return(json.loads(self.cw))

# Rep "user" data. For fast access to user data
class RepSecret(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=20)
    group = models.CharField(max_length=20, default='unspec')
    first_used = models.DateTimeField('when first used')
    last_used = models.DateTimeField('when last used')
    rep_score = models.FloatField(default=1.0)
    # raw data
    num_subs = models.IntegerField(default=0)
    num_mods = models.IntegerField(default=0)
    acc_yays = models.FloatField(default=0.0) #models.IntegerField(default=0) # also counts own subs
    acc_nays = models.FloatField(default=0.0) #models.IntegerField(default=0)
    inacc_yays = models.FloatField(default=0.0) #models.IntegerField(default=0) # also counts own subs
    inacc_nays = models.FloatField(default=0.0) #models.IntegerField(default=0)
    # constructor
    @classmethod
    def create(cls, rep_secret, group):
        rep = cls(
            id = str(uuid.uuid1()),
            name = rep_secret,
            group = group,
            first_used = datetime.now(timezone.utc),
            last_used = datetime.now(timezone.utc)
        )
        rep.save()
        return(rep)
    # to string
    def __str__(self):
        return(self.name)
    # update fields
    def submit(self):
        self.last_used = datetime.now(timezone.utc)
        self.num_subs += 1
        self.save()
    def mod(self):
        self.last_used = datetime.now(timezone.utc)
        self.num_mods += 1
        self.save()
    # helper functions
    def subs_list(self):
        subs = list(Submission.objects.filter(group=self.group, rep_secret=self.name))
        return(sorted([s.rep_stats() for s in subs], key=lambda x : x['dt_sub'], reverse=True))
    def yays(self):
        return(self.acc_yays + self.inacc_yays)
    def nays(self):
        return(self.acc_nays + self.inacc_nays)
    def tot_known(self):
        return(self.acc_yays + self.acc_nays + self.inacc_yays + self.inacc_nays)
    def accuracy(self):
        if self.tot_known() == 0:
            return(0.0)
        return((self.acc_yays + self.acc_nays)/(self.tot_known()))
    def t1_error(self): # too strict
        if self.tot_known() == 0:
            return(0.0)
        return(self.inacc_nays / self.tot_known())
    def t2_error(self): # too lenient
        if self.tot_known() == 0:
            return(0.0)
        return(self.inacc_yays / self.tot_known())
    def get_score(self):
        return(self.rep_score)
    def calc_score(self):
        # Graph of score vs accuracy: https://www.desmos.com/calculator/yjyw5uamih
        score_ceiling = 5 # must change co[] if change this
        max_mods = 100
        max_days = 30
        mod_score_contrib = 0.8 # frac out of 1 (rest goes to age score)
        mod_score = (mod_score_contrib * score_ceiling) * min((self.num_mods / max_mods), 1.0)
        age_score = ((1 - mod_score_contrib) * score_ceiling) \
                    * min((self.last_used - self.first_used).total_seconds() / (max_days*24*60*60), 1.0)
        xp = mod_score + age_score
        acc = self.accuracy()
        co = [0.6, 0.3, 0.1] # for ideal short and long term behavior for f(xp, acc). f range: [0, 5]
        self.rep_score = (co[0]*xp)*acc**3 + (co[1]*xp)*acc**2 + (co[2]*xp)*acc + 1 - 0.2*xp
        self.save()
        #print(self, 'mod:', mod_score, 'age:', age_score, 'acc:', acc, 'score:', (co[0]*xp)*acc**3 + (co[1]*xp)*acc**2 + (co[2]*xp)*acc + 1 - 0.2*xp, flush=True)
        #print('1st:', (co[0]*xp)*acc**3, '2nd:', (co[1]*xp)*acc**2, '3rd:', (co[2]*xp)*acc, 'rest:', 1 - 0.2*xp, flush=True)
        return(self.rep_score)
    # return stat percentiles (t1_error, t2_error, rep-score)
    def percentiles(self):
        reps = list(RepSecret.objects.filter(group=self.group))
        ordered_t1err = [r.t1_error() for r in sorted(reps, key=lambda r : r.t1_error(), reverse=True)]
        t1err_pct = ordered_t1err.index(self.t1_error()) / len(ordered_t1err) * 100
        ordered_t2err = [r.t2_error() for r in sorted(reps, key=lambda r : r.t2_error(), reverse=True)]
        t2err_pct = ordered_t2err.index(self.t2_error()) / len(ordered_t2err) * 100
        ordered_score = [r.get_score() for r in sorted(reps, key=lambda r : r.get_score())]
        score_pct = ordered_score.index(self.get_score()) / len(ordered_score) * 100
        #self.calc_score() # can delete this later
        return((t1err_pct, t2err_pct, score_pct))

# Info per confessions group
class Group(models.Model):
    name = models.CharField(primary_key=True, max_length=20)
    color1 = models.CharField(max_length=7, default='#ffffff') # banner text
    color2 = models.CharField(max_length=7, default='#000000') # banner background
    color3 = models.CharField(max_length=7, default='#000000') # highlighted text
    color4 = models.CharField(max_length=7, default='#dddddd') # page background
    timezone = models.CharField(max_length=20, null=True, blank=True)
    token = models.CharField(max_length=512, null=True, blank=True)
    # stats
    next_num = models.IntegerField(default=1)
    num_posts = models.IntegerField(default=0)
    avg_delay = models.FloatField(default=0.0)
    visits = models.IntegerField(default=0)
    # Linked platforms
    fb_page_id = models.CharField(max_length=30, null=True, blank=True)
    fb_url = models.CharField(max_length=100, default='https://facebook.com')
    ig_user_id = models.CharField(max_length=30, null=True, blank=True)
    ig_url = models.CharField(max_length=100, default='https://instagram.com')
    # status: ('GREEN'-accepting & posting, 'YELLOW'-only accepting, 'RED'-not accepting nor posting)
    status = models.CharField(max_length=10, default='GREEN')
    # make new post
    def inc_num(self):
        num = self.next_num
        self.next_num += 1
        self.save()
        return(num)
    # adjust avg delay
    def add_post(self, new_delay):
        tot_delay = self.avg_delay * self.num_posts + new_delay
        self.num_posts += 1
        self.avg_delay = tot_delay / self.num_posts
        self.save()
