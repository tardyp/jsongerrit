def download_all(gerrit):
    l = gerrit.ChangeListService.allOpenNext("z",100)
    #l = gerrit.ChangeListService.allClosedNext("MERGED","z",100)
    for i in l.result.changes:
        l = gerrit.ChangeDetailService.changeDetail({"id":i.id.id})
        #print l
        print "repo download %s %s/%s  \t# %s %s"%(i.project.key.name, 
                                                   l.result.currentPatchSetId.changeId.id,
                                                   l.result.currentPatchSetId.patchSetId,
                                                   l.result.currentDetail.info.committer.when.split(" ")[0],
                                                   l.result.currentDetail.info.subject)
