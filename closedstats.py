import httplib,traceback
import sys,re
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

automatic_filters = [
    "Your change could not be merged due to a path conflict.",
    "Patch Set",
    "Uploaded patch set",
    "Looks good to me, approved",
    "Looks good to me, but someone else must approve",
    "Verified",
    "Looks good to me, approved",
    "Change has been successfully merged into the git repository.",
    "Your change could not be merged due to a path conflict.",
    "Please merge (or rebase) the change locally and upload the resolution for review.",
    "Your change requires a recursive merge to resolve.",
    ]
non_chars_re = re.compile('[^a-zA-Z]')
def count_non_auto_messages(messages):
    count = 0
    for i in messages:
        m = i.message
        for filt in automatic_filters:
            m = m.replace(filt,"")
        m = non_chars_re.sub("",m)
        if m.startswith("buildbotfinishedcompilingyourpatchsetonconfiguration"):
            continue
        if len(m)>1:
            count+=1
            m = i.message

    return count
class CSV:
    csv_line = ""
    csv_head = ""
    csv_head_printed = False
    def __init__(self,filename,filename2):
        self.f = open(filename,"w")
        self.f2 = open(filename2,"w")
        self.stats = {}
    def add_val(self,title, val,do_stats=0):
        if type(val) == type(""):
            self.csv_line += '"%s";'%(val.replace(";",","))
        else:
            self.csv_line += '%d;'%(val)
        self.csv_head += '"%s";'%(title)
        if do_stats:
            k = "%s=%d"%(title,val)
            if self.stats.has_key(k):
                self.stats[k]+=1
            else:
                self.stats[k]=1
    def end_line(self):
        if not self.csv_head_printed:
            self.csv_head_printed = True
            self.f.write(self.csv_head)
            self.f.write("\n")
        self.f.write(self.csv_line)
        self.f.write("\n")
        self.f.flush()
        self.csv_head = ""
        self.csv_line = ""
    def end_csv(self):
        for k,v, in sorted([(k,v) for k,v in self.stats.items()]):
            self.f2.write("%s;%d\n"%(k,v))
        self.f2.close()
        self.f.close()
def closedstats(gerrit):
    global message_list
    last = "z"
    csv = CSV("closed_list.csv","closed_stats.csv")
    while True:
        l = gerrit.ChangeListService.allQueryNext("status:merged",last,10)
        if len(l.result.changes) == 0:
            break
        for i in l.result.changes:
            details = gerrit.ChangeDetailService.changeDetail({'id':i.id.id})
            print i.id.id ,i.subject
            csv.add_val("changeid:",i.id.id)
            csv.add_val("subject:",i.subject[:80])
            csv.add_val("owner:",get_user_name(details,details.result.change.owner.id))
            csv.add_val("merger:",get_merger(details))
            csv.add_val("project:",details.result.change.dest.projectName.name + ":"+ details.result.change.dest.branchName)
            csv.add_val("num_messages:",len(details.result.messages),do_stats=1)
            csv.add_val("num_non_auto_messages:",count_non_auto_messages(details.result.messages),do_stats=1)
            csv.add_val("num_approvals:",len(details.result.approvals),do_stats=1)
            csv.add_val("num_patchsets:",details.result.change.nbrPatchSets,do_stats=1)
            csv.add_val("subject_greater_than_80:",len(i.subject)>80,do_stats=1)
            csv.end_line()
            last = i.sortKey
    csv.end_csv()
