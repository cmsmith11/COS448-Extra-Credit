#!/usr/bin/env python3
import sys
from models import CONFESSION, COMMENT, REPLY
from models import to_local_time, short_dt
sys.path.append('../tcx')
from tcx import settings
import json
import psycopg2
import requests

def db_connect(db_info):
	conn = psycopg2.connect(
		host=db_info['HOST'],
		database=db_info['NAME'],
		user=db_info['USER'],
		password=db_info['PASSWORD']
	)
	cur = conn.cursor()
	return(conn, cur)

def get_db_tups(cur, group_name):
	cur.execute('SELECT id, fb_id, ig_id FROM secport_submission WHERE "group" = \'' + group_name + '\' AND status = \'accepted\'')
	return(cur.fetchall())

def get_group_platform_info(cur, group_name):
	cur.execute('SELECT token, fb_page_id, ig_user_id FROM secport_group WHERE name = \'' + group_name + '\'')
	return(cur.fetchone())

def get_fbids(fb_page_id, token):
	after = ''
	fbids = set()
	while True:
		URL = "https://graph.facebook.com/{}/feed?access_token={}&limit=100&fields=id&after={}".format(fb_page_id, token, after)
		r = requests.get(URL)
		fb_json = json.loads(r.text)
		for i in fb_json['data']:
			fbids.add(i['id'])
		if 'next' in fb_json['paging']:
			after = fb_json['paging']['cursors']['after']
		else:
			break
	return(fbids)

# return list of all posted ids on ig
def get_igids(ig_user_id, token):
	after = ''
	igids = set()
	while True:
		URL = "https://graph.facebook.com/{}/media?access_token={}&limit=100&fields=id&after={}".format(ig_user_id, token, after)
		r = requests.get(URL)
		ig_json = json.loads(r.text)
		for i in ig_json['data']:
			igids.add(i['id'])
		if 'next' in ig_json['paging']:
			after = ig_json['paging']['cursors']['after']
		else:
			break
	return(igids)

# return dict containing sub ids per platform of subs in db but not platform
def get_to_post(db_tups, fbids, igids):
	to_post = {
		'fb': [],
		'ig': []
	}
	for subid, fbid, igid in db_tups:
		if fbid == None or fbid not in fbids:
			# sub in db not on fb
			to_post['fb'].append(subid)
		if igid == None or igid not in igids:
			# sub in db not on ig
			to_post['ig'].append(subid)
	return(to_post)

def get_sub_type(parent_id, grandparent_id):
	if parent_id == None:
		return CONFESSION
	elif grandparent_id == None:
		return COMMENT
	else:
		return REPLY

def get_post_info(cur, group_name, subid, token):
	cur.execute('SELECT parent_id, sub_num, toggle, cw, content, dt_sub FROM secport_submission WHERE id = \'' + subid + '\'')
	sub = cur.fetchone()

	parent_id = sub[0]
	grandparent_id = None
	if parent_id != None:
		cur.execute('SELECT parent_id FROM secport_submission WHERE id = \'' + parent_id + '\'')
		grandparent_id = cur.fetchone()[0]

	post_info = {
		'group': group_name,
		'type': get_sub_type(parent_id, grandparent_id),
		'sub_num': sub[1],
		'as_op': parent_id != None and sub[2],
		'cw': json.loads(sub[3]),
		'content': sub[4],
		'dt_sub': 3,#sub.short_local_dt(sub.dt_sub),
		'token': token
	}
	return(post_info)


def main():

	if len(sys.argv) != 2:
		print('usage: ./sync.py [GROUP]')
		exit()

	group_name = sys.argv[1]

	# connect to database
	db_info = settings.DATABASES['default']
	conn, cur = db_connect(db_info)

	# Get list of all tuples containing all platform ids in DB
	db_tups = get_db_tups(cur, group_name)

	# get group platform data
	token, fb_page_id, ig_user_id = get_group_platform_info(cur, group_name)

	# close db connections
	cur.close()
	conn.close()

	# collect facebook page post ids (fbids)
	fbids = get_fbids(fb_page_id, token)

	# collect instagram post ids (igids)
	igids = get_igids(ig_user_id, token)

	# create 2n lists (n is number of linked platforms) n post, and n delete lists
	to_delete = {
		'fb': [],
		'ig': []
	}

	# iterate through db, adding to corresponding post lists
	to_post = get_to_post(db_tups, fbids, igids)

	# iterate n times through each platform, adding to delete list
	db_fbs = [i[1] for i in db_tups]
	for i in fbids:
		if i not in db_fbs:
			to_delete['fb'].append(i)

	db_igs = [i[2] for i in db_tups]
	for i in igids:
		if i not in db_igs:
			to_delete['ig'].append(i)

	# for each platform, delete all on delete list, post all on post list


if __name__ == "__main__":
	#main()
	print('done')
