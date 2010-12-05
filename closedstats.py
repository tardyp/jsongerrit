import httplib
def get_user_name(details, id):
    for i in details.result.accounts.accounts:
        if i.has_key('fullName'):
            if i.id.id == id:
                return repr(i.fullName)
def get_merger(details):
    for j in details.result.approvals:
        for i in j.approvals:
            if i.key.categoryId.id == "SUBM":
                return get_user_name(details,i.key.accountId.id)
    return ""
def closedstats(gerrit):
    last = "z"
    while True:
        try:
            l = gerrit.ChangeListService.allQueryNext("status:merged",last,100)
        except:
            continue
        for i in l.result.changes:
            details = gerrit.ChangeDetailService.changeDetail({'id':i.id.id})
            print "changeid:",i.id.id,
            print "owner:",get_user_name(details,details.result.change.owner.id),
            print "merger:",get_merger(details),
            print "project:",details.result.change.dest.projectName.name,details.result.change.dest.branchName,
            print "num_messages:",len(details.result.messages),
            print "num_approvals:",len(details.result.approvals),
            print "num_patchsets:",details.result.change.nbrPatchSets
            last = i.sortKey
